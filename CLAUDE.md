# CLAUDE.md

This file provides guidance to [Claude Code](https://claude.com/claude-code) when working with code in this repository.

## Status: pre-bootstrap

This repo currently tracks only `LICENSE`, `.gitignore`, and this `CLAUDE.md`. The full scaffolding spec lives in **[issue #1](https://github.com/agentculture/tipalti/issues/1)** — a Claude Code session is expected to execute it end-to-end on a single feature branch (`bootstrap/sibling-pattern`) and open a PR. `.claude/` will be introduced by the bootstrap PR.

Read issue #1 in full before doing any bootstrap work. It is the source of truth for package names, version (`0.0.1`), file layout, vendored skills, and CI workflows. Do not improvise — the issue exists so the bootstrap is reproducible.

## What tipalti will be

A PyPI-publishable CLI (`tipalti`) for Tipalti Solutions, scaffolded from the **AgentCulture sibling pattern**. Initial verbs per issue #1: `learn`, `explain`, `whoami` (auth probe stub — real Tipalti API auth lands later).

## Planned project shape (post-bootstrap)

Per issue #1 step 3, the bootstrap PR will land:

```text
tipalti/
├── __init__.py            # __version__ via importlib.metadata("tipalti")
├── __main__.py            # python -m tipalti
└── cli/
    ├── __init__.py        # argparse main
    ├── _errors.py         # TipaltiError + EXIT_USER_ERROR / EXIT_ENV_ERROR
    ├── _output.py         # emit_result / emit_error / emit_diagnostic
    └── _commands/
        ├── __init__.py
        ├── learn.py
        ├── explain.py
        └── whoami.py
tests/
├── test_cli_smoke.py
├── test_cli_learn.py
└── test_cli_whoami.py
```

## Planned commands (post-bootstrap)

These commands become live once the bootstrap PR merges. Until then they will fail (no `pyproject.toml`, no `tipalti/` package).

- Install: `uv sync`
- Test: `uv run pytest -n auto -v`
- Single test: `uv run pytest tests/test_cli_smoke.py::test_version -v`
- Lint: `uv run flake8 tipalti tests && uv run black --check . && uv run isort --check .`
- Markdown lint: `markdownlint-cli2 "**/*.md"`
- Self-check: `steward doctor . --scope self`
- Smoke: `uv run tipalti --version` (expects `0.0.1`) and `uv run python -m tipalti`
- Build: `uv build`
- Publish: handled by `.github/workflows/publish.yml` via PyPI Trusted Publishing on tag.

## Pattern sources (canonical, fetched over the network)

The bootstrap fetches files from these repos rather than assuming sibling checkouts on disk:

- **steward** (`agentculture/steward`) — pattern owner; source of `pyproject.toml`, CI workflows (`tests.yml`, `publish.yml`), `.markdownlint-cli2.yaml`, and all vendored skills.
- **afi-cli** (`agentculture/afi-cli`) — emits the agent-first CLI tree under `.afi/reference/python-cli/` (git-ignored). `MANIFEST.json` distinguishes `stable-contract` files (copy verbatim, substitute the three tokens `{{project_name}}` / `{{slug}}` / `{{module}}` → `tipalti`) from `shape-adapt` files (use as structural model, rewrite content).

Do **not** assume `../steward` or `../afi-cli` exist locally.

## Tooling baseline (post-bootstrap)

- **uv** for env + dependency management; **hatchling** build backend
- **pytest** with `pytest-xdist` (`uv run pytest -n auto -v`)
- **flake8 / black / isort / bandit** for Python lint
- **markdownlint-cli2** with repo-local `.markdownlint-cli2.yaml`
- CI: `tests.yml` (pytest + lint + `version-check`) and `publish.yml` (PyPI Trusted Publishing + TestPyPI dev builds on PRs)

## Conventions to preserve

- **Every PR bumps the version.** The `version-check` job in `tests.yml` enforces this against `origin/main`. Use the vendored `version-bump` skill.
- **Skills 3-rule contract:** each `.claude/skills/<name>/` directory must contain `SKILL.md` (frontmatter `name` matches directory name) and a sibling `scripts/` directory; no external/per-user path dependencies in committed skill code.
- **Portability:** no `/home/<user>/...` paths, no per-user dotfile refs in tracked files. `steward doctor . --scope self` must exit 0.
- **All-backends rule** (inherited from the AgentCulture ecosystem): if/when tipalti grows multi-backend surface, a feature added to one backend must be propagated to all. A feature in only one backend is a bug.

## After the bootstrap PR merges (manual, one-time)

These cannot be automated and should be left as a checklist comment on the bootstrap PR:

1. Configure **PyPI Trusted Publishing** for `tipalti` ← `agentculture/tipalti`, environment `pypi`, workflow `publish.yml`. Same for **TestPyPI**.
2. Create GitHub Environments `pypi` and `testpypi` on the repo.
3. Branch protection on `main`: require `tests` and `version-check` jobs.

## Updating this file

Once the bootstrap PR merges, drop the "Planned" qualifier from the **project shape** and **commands** sections, and replace **Status** with a one-line statement of current state. The "Pattern sources", "Conventions to preserve", and "After the bootstrap PR merges" sections remain useful indefinitely.
