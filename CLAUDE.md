# CLAUDE.md

This file provides guidance to [Claude Code](https://claude.com/claude-code) when working with code in this repository.

## Status

`v0.2.0` — broadens read-only REST v2 coverage. Corrects the resource path prefix from `/v2/` to the documented `/api/v1/`, removes the `bill` noun (bills are unified under invoices upstream; `/v2/bills` never existed), and adds read-only `list`/`get` verbs for Payments, Payer Entities, GL Accounts, Custom Fields, Payment Terms, and Tax Codes. `whoami` now probes `/api/v1/payer-entities` (REST v2 has no identity endpoint) and reports reachability + auth only. Payment batches and OAuth scope handling are deferred; mutations, iFrame URL generation, webhooks, SOAP, tax forms, and KYC remain deferred to subsequent releases.

`v0.1.0` — first real release. Added read-only verbs over Tipalti REST v2 (Payees, Invoices, Bills), OAuth2 client-credentials auth via env vars, and a real `whoami` probe.

Scaffolded from the AgentCulture sibling pattern. Manual one-time setup (already completed for the v0.0.1 bootstrap PR):

1. Configure **PyPI Trusted Publishing** for `tipalti` ← `agentculture/tipalti`, environment `pypi`, workflow `publish.yml`. Same for **TestPyPI**.
2. Create GitHub Environments `pypi` and `testpypi` on the repo.
3. Branch protection on `main`: require `tests` and `version-check` jobs.

## What this project is

`tipalti` is the CLI for Tipalti Solutions, scaffolded from the AgentCulture sibling pattern (the same shape used by [`steward`](https://github.com/agentculture/steward) and the agent-first CLI tree from [`afi-cli`](https://github.com/agentculture/afi-cli)). v0.2.0 ships a read-only explorer over Tipalti REST v2 (Payees, Invoices, Payments, Payer Entities, GL Accounts, Custom Fields, Payment Terms, Tax Codes) plus the agent-first affordances (`learn`, `explain`, `whoami`); payment batches, OAuth scope handling, mutations, iFrame URL generation, webhooks, SOAP, tax forms, and KYC land in subsequent releases.

The first resident user of this CLI is an LLM agent. Every verb supports `--json`, default human-mode output is markdown, errors carry machine-readable remediation hints, and one verb invocation = one upstream HTTP request (auth excluded). State lives in env vars; the only persistent file is the bearer-token cache.

The repo is intentionally portable: it assumes nothing about local sibling checkouts. `pyproject.toml`, CI workflows, and skills are pulled from steward over the network at bootstrap time, then committed verbatim (or with the documented token substitutions). `steward doctor . --scope self` enforces this on every PR.

## Auth and environment

Tipalti REST v2 uses OAuth 2.0 client credentials. The CLI reads:

- `TIPALTI_CLIENT_ID` / `TIPALTI_CLIENT_SECRET` — required.
- `TIPALTI_ENV` — `sandbox` | `production`; default `sandbox`.
- `TIPALTI_API_BASE` / `TIPALTI_TOKEN_URL` — optional URL overrides.

Bearer tokens are cached at `$XDG_CACHE_HOME/tipalti/token-<env>.json` (file mode `0600`). The cache is a pure performance optimization: delete the file to force re-auth. Rotating the client ID invalidates the cache automatically (the cache record carries a hash of the client ID).

`tipalti whoami` is a probe, not a gate: missing creds and `401` both report `unauthenticated` and exit `0`.

There is one opt-in integration test (`@pytest.mark.integration`) that hits the real sandbox if `TIPALTI_CLIENT_ID/SECRET` and `TIPALTI_ENV=sandbox` are set; it is skipped by default and not run in CI.

## Project shape

Distributed as **`tipalti`** on PyPI (Trusted Publishing). The Python package is `tipalti`; the binary is `tipalti`. Layout follows the afi-cli pattern (top-level package, no `src/`):

```text
tipalti/                    # Python package (pip install tipalti)
├── __init__.py             # __version__ via importlib.metadata("tipalti")
├── __main__.py             # python -m tipalti
├── api/                    # CLI-agnostic httpx client over Tipalti REST v2
│   ├── _env.py             # reads TIPALTI_CLIENT_ID/SECRET/ENV; URL defaults + overrides
│   ├── auth.py             # OAuth2 client-creds + on-disk token cache
│   ├── client.py           # TipaltiClient + payees/invoices/bills resource groups
│   └── errors.py           # HTTP-status → AfiError mapping
└── cli/
    ├── __init__.py         # argparse main(); registers all noun groups
    ├── _errors.py          # AfiError + EXIT_USER_ERROR / EXIT_ENV_ERROR
    ├── _output.py          # emit_result / emit_error + markdown render helpers
    ├── _listing.py         # shared list/get verb handler
    └── _commands/          # subcommand modules; each has register(sub) + handler
        ├── learn.py        # `tipalti learn`
        ├── explain.py      # `tipalti explain <path>`
        ├── whoami.py       # `tipalti whoami` — real auth probe
        ├── payee.py        # `tipalti payee {list,get}`
        ├── invoice.py      # `tipalti invoice {list,get}`
        ├── payment.py      # `tipalti payment {list,get}`
        ├── payer_entity.py # `tipalti payer-entity {list,get}`
        ├── gl_account.py   # `tipalti gl-account {list,get}`
        ├── custom_field.py # `tipalti custom-field {list,get}`
        ├── payment_term.py # `tipalti payment-term {list,get}`
        └── tax_code.py     # `tipalti tax-code {list,get}`
tipalti/explain/            # markdown catalog driving `explain`
├── __init__.py             # resolve() + known_paths()
└── catalog.py              # ENTRIES dict (root, auth, per-noun, per-verb)
tests/                      # pytest suite (split per-verb + api unit tests)
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
- **Smoke:** `uv run tipalti --version` (expects `0.2.0`) and `uv run python -m tipalti`.
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
