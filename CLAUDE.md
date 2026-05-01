# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Status: pre-bootstrap

This repo currently contains only `LICENSE`, `.gitignore`, and `.claude/`. The full scaffolding spec lives in **[issue #1](https://github.com/agentculture/tipalti/issues/1)** — a Claude Code session is expected to execute it end-to-end on a single feature branch (`bootstrap/sibling-pattern`) and open a PR.

Read issue #1 in full before doing any bootstrap work. It is the source of truth for package names, version (`0.0.1`), file layout, vendored skills, and CI workflows. Do not improvise — the issue exists so the bootstrap is reproducible.

## What tipalti will be

A PyPI-publishable CLI (`tipalti`) for Tipalti Solutions, scaffolded from the **AgentCulture sibling pattern**. Initial verbs per issue #1: `learn`, `explain`, `whoami` (auth probe stub — real Tipalti API auth lands later).

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

Once the bootstrap PR lands, replace the **Status** and **What tipalti will be** sections with concrete commands (build, test, single-test invocation, lint, publish) and a real architecture overview drawn from the actual code. The "Pattern sources", "Conventions to preserve", and "After the bootstrap PR merges" sections remain useful indefinitely.
