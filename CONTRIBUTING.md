# Contributing to ESO Armory

Bug reports, ideas, docs fixes and code are welcome. A security problem goes to
a [private report](SECURITY.md), not an issue.

## Ways to help

- **Report a bug** or **suggest a feature** in
  [issues](https://github.com/spanthetree/eso-armory/issues).
- **For anything larger,** such as a new feature, a new dependency or a change to the
  database or API, open an issue before you write much code.

## Setting up

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/spanthetree/eso-armory.git && cd eso-armory
uv sync --dev
make assets              # game icons from UESP
make playwright-install  # browsers for the UI tests
uv run server.py         # http://localhost:5000
```

[docs/architecture.md](docs/architecture.md) explains how the server, storage
and API fit together.

Never commit real SavedVariables, screenshots or logs from a live account.
Use the sanitized fixtures in `tests/fixtures/`. Never commit game artwork
either: add icons to `scripts/assets_manifest.json` instead.

## Checks

```bash
make test-all   # unit, API and Playwright tests
```

CI runs these on every pull request.

## Branches and pull requests

- Make every change on a new branch cut from a freshly pulled `master`.
- One pull request per issue.
- Before you open the PR, the branch's last change must:
  - add a dated section to `CHANGELOG.md`;
  - update `README.md` if anything user-facing changed;
  - bump the version in `pyproject.toml` and run `uv lock`.
- A change to the API, storage or security model updates
  [docs/architecture.md](docs/architecture.md) in the same PR.

## Licensing your contribution

ESO Armory is source-available under the
[PolyForm Noncommercial License 1.0.0](LICENSE): anyone may use, copy, change
and share it for any noncommercial purpose.

So that the maintainer can keep every version under one license, and offer it
under other terms later (a hosted version, say), contributions come in under a
wider grant than the one they go out under. By opening a pull request or
otherwise submitting a contribution, you agree that:

- you wrote it, or otherwise have the right to submit it;
- you license it to the maintainer, spanthetree, under the
  [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), as well as
  to everyone under the project's license; and
- you keep the copyright in it.

If you can't agree to that, say so in the pull request before it is merged.
