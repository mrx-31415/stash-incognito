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
Its end-to-end test against a real Stash, with Curator installed beside it, stays in
stash-curator (`tests/integration/test_incognito.py`).

```bash
python -m pytest tests          # needs pytest and node
python scripts/build.py         # dist/incognito.zip and dist/incognito-index.yml
python scripts/build.py --dev   # the dev source in dist/dev/
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org/):
release-please bumps `version:` in `incognito/incognito.yml`, updates
`incognito/CHANGELOG.md` and tags `incognito-vX.Y.Z`; the release workflow then
attaches `incognito.zip` and `incognito-index.yml`, which the plugin hub mirrors.

## License

[AGPL-3.0](LICENSE)
