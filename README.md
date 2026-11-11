# Incognito

**Watch without a trace.** Incognito is a small [Stash](https://github.com/stashapp/stash)
plugin that adds a switch to Stash's navbar. While it is on, this browser records no
plays: Stash saves no resume point, play count or history, and
[Stash Curator](https://github.com/mrx-31415/stash-curator) learns nothing from what you
watch. Curator is optional.
[Details](https://mrx-31415.github.io/stash-curator/privacy/#pausing-and-forgetting-viewing)

## Install

Add this plugin source under **Settings > Plugins > Available Plugins**, then install
**Incognito** and reload plugins:

```text
https://mrx-31415.github.io/stash-plugins/main/index.yml
```

Installs from the Stash Curator source
(`https://mrx-31415.github.io/stash-curator/index.yml`) keep receiving updates there.

Development builds from `main`: `https://mrx-31415.github.io/stash-incognito/dev/index.yml`.

## Development

Incognito was developed in [stash-curator](https://github.com/mrx-31415/stash-curator)
until 1.0.1; references like `mrx-31415/stash-curator#478` in the history point there.
Its test with Curator installed beside it (Curator records nothing either) stays in
stash-curator (`tests/integration/test_incognito.py`).

```bash
python -m pytest tests --ignore=tests/integration   # unit tests; needs pytest and node
python scripts/build.py         # dist/incognito.zip and dist/incognito-index.yml
python scripts/build.py --dev   # the dev source in dist/dev/
```

The integration tests run the built plugin in a throwaway Stash (Docker), play a
synthetic clip through Stash's own player with Playwright, and check both the
tracking requests and what Stash recorded:

```bash
pip install -r tests/integration/requirements.txt && playwright install chromium
scripts/integration                                  # against stashapp/stash:v0.31.1
STASH_IMAGE=stashapp/stash:latest scripts/integration
```

`KEEP_STASH=1` leaves the Stash running afterwards. CI runs them against v0.31.1 and
`latest`.

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
release-please bumps `version:` in `incognito/incognito.yml`, updates
`incognito/CHANGELOG.md` and tags `incognito-vX.Y.Z`; the release workflow then
attaches `incognito.zip` and `incognito-index.yml`, which the plugin hub mirrors.

## License

[AGPL-3.0](LICENSE)
