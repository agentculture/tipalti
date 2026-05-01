# CLAUDE.md

This file provides guidance to [Claude Code](https://claude.com/claude-code) when working with code in this repository.

## Status

Scaffolded from the AgentCulture sibling pattern at `v0.0.1`. The bootstrap PR (`bootstrap/sibling-pattern`, see `agentculture/tipalti#1`) lands the package, CI, and vendored skills described below. Manual one-time setup after the bootstrap PR merges:

1. Configure **PyPI Trusted Publishing** for `tipalti` ← `agentculture/tipalti`, environment `pypi`, workflow `publish.yml`. Same for **TestPyPI**.
2. Create GitHub Environments `pypi` and `testpypi` on the repo.
3. Branch protection on `main`: require `tests` and `version-check` jobs.

## What this project is

`tipalti` is the CLI for Tipalti Solutions, scaffolded from the AgentCulture sibling pattern (the same shape used by [`steward`](https://github.com/agentculture/steward) and the agent-first CLI tree from [`afi-cli`](https://github.com/agentculture/afi-cli)). v0.0.1 ships only the agent-first affordances (`learn`, `explain`) and an auth-probe stub (`whoami`); domain verbs that exercise the Tipalti API land in subsequent releases.

The repo is intentionally portable: it assumes nothing about local sibling checkouts. `pyproject.toml`, CI workflows, and skills are pulled from steward over the network at bootstrap time, then committed verbatim (or with the documented token substitutions). `steward doctor . --scope self` enforces this on every PR.

## Project shape

Distributed as **`tipalti`** on PyPI (Trusted Publishing). The Python package is `tipalti`; the binary is `tipalti`. Layout follows the afi-cli pattern (top-level package, no `src/`):

```text
tipalti/                    # Python package (pip install tipalti)
├── __init__.py             # __version__ via importlib.metadata("tipalti")
├── __main__.py             # python -m tipalti
└── cli/
    ├── __init__.py         # argparse main(); _ArgumentParser, _dispatch
    ├── _errors.py          # AfiError + EXIT_USER_ERROR / EXIT_ENV_ERROR
    ├── _output.py          # emit_result / emit_error / emit_diagnostic
    └── _commands/          # subcommand modules; each has register(sub) + handler
        ├── learn.py        # `tipalti learn` — agent-affordance prompt
        ├── explain.py      # `tipalti explain <path>` — markdown catalog lookup
        └── whoami.py       # `tipalti whoami` — auth probe stub (v0.0.1)
tipalti/explain/            # markdown catalog driving `explain`
├── __init__.py             # resolve() + known_paths()
└── catalog.py              # ENTRIES dict
tests/                      # pytest suite (split per-verb)
.claude/skills/             # vendored from steward (see "Skills convention")
.github/workflows/          # tests.yml + publish.yml (OIDC Trusted Publishing)
pyproject.toml              # version source-of-truth
CHANGELOG.md                # Keep-a-Changelog
```

## Build / test / publish

- **Install for dev:** `uv sync` (or `uv pip install -e .` then `uv pip install --group dev`).
- **Run CLI from source:** `uv run tipalti --version` / `uv run python -m tipalti`.
- **Tests:** `uv run pytest -n auto -v`. CI runs on every PR + push to main.
- **Single test:** `uv run pytest tests/test_cli_smoke.py::test_version_flag -v`.
- **Lint:** `uv run flake8 tipalti tests && uv run black --check . && uv run isort --check .`
- **Markdown lint:** `markdownlint-cli2 "**/*.md"` (uses repo-local `.markdownlint-cli2.yaml`).
- **Self-check:** `steward doctor . --scope self`.
- **Smoke:** `uv run tipalti --version` (expects `0.0.1`) and `uv run python -m tipalti`.
- **Build:** `uv build`.
- **Version bump:** `python3 .claude/skills/version-bump/scripts/bump.py {patch|minor|major}` — updates `pyproject.toml` and prepends a CHANGELOG entry. **Required on every PR** (the `version-check` CI job comments on the PR and fails the run if the version matches main; AgentCulture rule, no exceptions for docs/config-only changes).
- **Publish:** push to `main` triggers `.github/workflows/publish.yml` → builds with `uv build` → publishes `tipalti` to PyPI via Trusted Publishing (no API tokens). PRs publish a `.dev<run_number>` to TestPyPI for smoke-testing. Fork PRs are skipped (no OIDC context).

## Conventions in use

- **Packaging:** `uv` + `pyproject.toml` (hatchling backend), `[project.scripts]` entry point.
- **Tests:** `pytest` (xdist + cov-xml in CI). Tests live under `tests/`.
- **Lint:** `flake8`, `bandit`, `black`, `isort`. Run via uv (`uv run black tipalti tests`, etc.).
- **Versioning:** single source of truth in `pyproject.toml`. `tipalti.__version__` is read at import time from package metadata — there is no separate `__version__` literal to keep in sync.
- **Markdown:** `markdownlint-cli2` against the repo-local `.markdownlint-cli2.yaml`. Don't depend on a per-user home-directory config.

## Skills convention (3-rule contract)

Every skill in `.claude/skills/<name>/` ships:

1. `SKILL.md` — explains *why* and *when* to use it. Frontmatter `name:` matches the directory name; short prose; no inline 10-step walk-throughs.
2. `scripts/<entry-point>.sh` (or `.py`) — the script that automates the workflow. Following the skill should be "run this script," not "do these ten manual steps." If a skill doesn't have a script, write one before relying on it.
3. **No external path dependencies.** Scripts must not reach into another skill's home-directory copy or any other location outside this repo. If a skill needs functionality from elsewhere, vendor it into the skill's own `scripts/` directory. This makes skills portable across AgentCulture projects.

Per-machine paths live in **`.claude/skills.local.yaml`** (git-ignored). A committed `.claude/skills.local.yaml.example` documents every key. Skills read the local file, falling back to the example when the local copy hasn't been created yet.

`steward doctor . --scope self` enforces both the portability rule (no `/home/<user>/...` paths or per-user dotfile refs in tracked files) and the skills 3-rule contract on every PR.

## All-backends rule (inherited)

If/when tipalti grows multi-backend surface (e.g. multiple Tipalti API auth flows, multiple agent harnesses), the AgentCulture all-backends rule applies: a feature added to one backend must be propagated to all. A feature in only one backend is a bug.

## Pattern sources (canonical, fetched over the network)

- **steward** (`agentculture/steward`) — pattern owner; canonical source of `pyproject.toml`, CI workflows, `.markdownlint-cli2.yaml`, and the vendored skills under `.claude/skills/`.
- **afi-cli** (`agentculture/afi-cli`) — emits the agent-first CLI tree under `.afi/reference/python-cli/` (git-ignored). `MANIFEST.json` distinguishes `stable-contract` files (copy verbatim, substitute `{{project_name}}` / `{{slug}}` / `{{module}}` → `tipalti`) from `shape-adapt` files (use as structural model, rewrite content for tipalti's verbs).

Do **not** assume `../steward` or `../afi-cli` exist locally. Bootstrap and re-vendoring fetch from `raw.githubusercontent.com`.
