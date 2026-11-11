"""Incognito in a real Stash: its navbar switch, and plays recorded or not.

The clip is played to its end through Stash's own player. With the switch off
(the control) Stash's activity tracker sends SceneSaveActivity and SceneAddPlay,
and the scene's play count, play duration and resume point change on the
server. With it on, none is sent and the server records nothing.
"""

from __future__ import annotations

import pytest
from conftest import PLUGIN_ID, dismiss_modals
from playwright.sync_api import Page, expect

TRACKING = ("SceneSaveActivity", "SceneAddPlay")
HISTORY = "query($id: ID!) { findScene(id: $id) { play_count play_duration resume_time } }"


@pytest.fixture
def fresh(gql, scene):
    """The scene with no play history, before and after the test."""

    def reset() -> None:
        gql("mutation($id: ID!) { sceneResetPlayCount(id: $id) }", {"id": scene["id"]})
        gql(
            "mutation($id: ID!) { sceneResetActivity(id: $id, reset_resume: true, "
            "reset_duration: true) }",
            {"id": scene["id"]},
        )

    reset()
    yield scene
    reset()


def history(gql, scene) -> dict:
    return gql(HISTORY, {"id": scene["id"]})["findScene"]


def toggle(page: Page):
    # Stash renders utility buttons in the navbar strip and again in the collapsible
    # menu; the switch belongs in the strip at every width.
    return page.locator(".navbar-buttons .incognito-toggle")


def test_stash_lists_the_plugin(gql) -> None:
    plugins = gql("{ plugins { id enabled tasks { name } hooks { name } settings { name } } }")
    plugin = next(p for p in plugins["plugins"] if p["id"] == PLUGIN_ID)
    assert plugin["enabled"]
    # UI only: no tasks, hooks or settings (Stash lists none as null).
    assert not (plugin["tasks"] or plugin["hooks"] or plugin["settings"]), plugin


@pytest.mark.parametrize("width", [1440, 390], ids=["desktop", "mobile"])
def test_the_switch_sits_with_stashs_navbar_buttons(page, base_url, width, errors) -> None:
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(base_url + "/scenes", wait_until="domcontentloaded")
    dismiss_modals(page)
    switch = toggle(page)
    expect(switch).to_be_visible()
    expect(switch).to_have_attribute("aria-pressed", "false")
    expect(page.locator(".navbar-collapse .incognito-toggle")).to_be_hidden()
    # Stash's own utility buttons survive the patch.
    expect(page.locator(".navbar-buttons a[href='/settings']")).to_have_count(1)
    new, row = page.locator(".navbar-buttons > .mr-2 .btn"), page.locator(".navbar-buttons")
    box, new_box, row_box = switch.bounding_box(), new.bounding_box(), row.bounding_box()
    assert box and new_box and row_box
    # Centred in the button row, as Stash's own buttons are, and not touching them.
    assert abs(box["y"] + box["height"] / 2 - (row_box["y"] + row_box["height"] / 2)) <= 1
    assert box["x"] >= new_box["x"] + new_box["width"] + 4
    assert errors == []


@pytest.mark.parametrize("incognito", [False, True], ids=["off", "on"])
def test_plays_are_recorded_only_with_the_switch_off(
    page, base_url, gql, fresh, incognito, errors
) -> None:
    sent: list[str] = []

    def record(request) -> None:
        if request.method != "POST" or not request.url.endswith("/graphql"):
            return
        payload = request.post_data_json or {}
        if payload.get("operationName") in TRACKING:
            sent.append(payload["operationName"])

    page.on("request", record)
    page.goto(base_url + "/", wait_until="domcontentloaded")
    dismiss_modals(page)
    if incognito:
        toggle(page).click()
        expect(toggle(page)).to_have_attribute("aria-pressed", "true")

    page.goto(f"{base_url}/scenes/{fresh['id']}", wait_until="domcontentloaded")
    dismiss_modals(page)
    # The switch belongs to the browser and survives page loads.
    expect(toggle(page)).to_have_attribute("aria-pressed", str(incognito).lower())
    video = page.locator(".video-js video")
    expect(video).to_have_count(1, timeout=30_000)
    video.evaluate("video => { video.muted = true; return video.play(); }")
    page.wait_for_function("() => document.querySelector('.video-js video')?.ended", timeout=30_000)
    page.wait_for_timeout(1500)
    page.goto(base_url + "/", wait_until="domcontentloaded")  # leaving sends the last save
    page.wait_for_timeout(2500)

    after = history(gql, fresh)
    if incognito:
        assert sent == []
        assert after == {"play_count": 0, "play_duration": 0, "resume_time": 0}, after
    else:
        assert set(sent) == set(TRACKING), sent
        assert after["play_count"] == 1 and after["play_duration"] > 0, after
    assert errors == []


def test_turning_it_on_mid_play_drops_what_was_pending(page, base_url, gql, fresh, errors) -> None:
    sent: list[str] = []
    page.on(
        "request",
        lambda r: (
            sent.append((r.post_data_json or {}).get("operationName"))
            if r.method == "POST" and r.url.endswith("/graphql")
            else None
        ),
    )
    page.goto(f"{base_url}/scenes/{fresh['id']}", wait_until="domcontentloaded")
    dismiss_modals(page)
    video = page.locator(".video-js video")
    expect(video).to_have_count(1, timeout=30_000)
    video.evaluate("video => { video.muted = true; return video.play(); }")
    page.wait_for_function("() => document.querySelector('.video-js video').currentTime > 2")
    toggle(page).click()
    expect(toggle(page)).to_have_attribute("aria-pressed", "true")
    page.wait_for_function("() => document.querySelector('.video-js video')?.ended", timeout=30_000)
    page.goto(base_url + "/", wait_until="domcontentloaded")
    page.wait_for_timeout(2500)
    assert not set(sent) & set(TRACKING), sent
    assert history(gql, fresh)["play_count"] == 0
    assert errors == []
