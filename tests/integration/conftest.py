"""Fixtures for the integration tests: a throwaway Stash started by
scripts/integration, with this plugin installed and one synthetic clip in its
library. pytest-playwright provides `page` and `base_url`."""

from __future__ import annotations

import contextlib
import json
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

import pytest

PLUGIN_ID = "incognito"

Gql = Callable[..., dict[str, Any]]


@pytest.fixture(scope="session")
def gql(base_url: str) -> Gql:
    def request(query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = json.dumps({"query": query, "variables": variables or {}}).encode()
        req = urllib.request.Request(
            f"{base_url}/graphql", data=payload, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as error:
            raise RuntimeError(f"Stash returned {error.code}: {error.read()[:500]!r}") from error
        if data.get("errors"):
            raise RuntimeError(f"GraphQL error: {data['errors']}")
        return data["data"]

    return request


def wait_for_job(gql: Gql, job_id: str, timeout: float = 120) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job = gql("query($id: ID!) { findJob(input: {id: $id}) { status error } }", {"id": job_id})
        job = job["findJob"]
        if job is None or job["status"] == "FINISHED":
            return
        if job["status"] in ("FAILED", "CANCELLED"):
            raise RuntimeError(f"job {job_id} {job['status']}: {job['error']}")
        time.sleep(0.5)
    raise TimeoutError(f"job {job_id} still running after {timeout}s")


@pytest.fixture(scope="session")
def scene(gql: Gql) -> dict[str, Any]:
    """The scanned synthetic clip: {"id", "duration"}."""
    # A fresh Stash opens its release notes once; a far-future "seen" date keeps them shut.
    gql("mutation($p: Map!) { configureUI(partial: $p) }", {"p": {"lastNoteSeen": 99991231}})
    query = "{ findScenes { scenes { id files { duration } } } }"
    found = gql(query)["findScenes"]["scenes"]
    if not found:
        wait_for_job(gql, gql("mutation { metadataScan(input: {}) }")["metadataScan"])
        found = gql(query)["findScenes"]["scenes"]
    assert len(found) == 1, found
    return {"id": found[0]["id"], "duration": found[0]["files"][0]["duration"]}


@pytest.fixture
def errors(page) -> list[str]:
    """JavaScript errors on the page during the test (the test asserts on them)."""
    found: list[str] = []
    page.on("pageerror", lambda error: found.append(str(error)))
    return found


def dismiss_modals(page) -> None:
    """Close any dialog a fresh Stash puts over the page."""
    for _ in range(5):
        if page.locator("div.modal.show").count() == 0:
            return
        for selector in ("div.modal.show .btn-close", "div.modal.show .close"):
            with contextlib.suppress(Exception):
                page.locator(selector).first.click(force=True, timeout=1000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
