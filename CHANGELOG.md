# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). This project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-05-01

### Added

- tipalti payee list / payee get — read-only Payees verbs (REST v2)
- tipalti invoice list / invoice get — read-only Invoices verbs
- tipalti bill list / bill get — read-only Bills verbs
- tipalti.api package — CLI-agnostic httpx client with OAuth2 client_credentials, on-disk token cache (`$XDG_CACHE_HOME/tipalti/token-<env>.json`, mode 0600), and HTTP-status → AfiError mapping
- Real tipalti whoami probe — exits 0 with status=unauthenticated when creds missing or 401
- Markdown render helpers in cli/_output.py (render_record_md, render_list_md, render_kv_md) — agent-friendly default human mode
- Env vars: TIPALTI_CLIENT_ID, TIPALTI_CLIENT_SECRET, TIPALTI_ENV (sandbox|production), optional TIPALTI_API_BASE / TIPALTI_TOKEN_URL overrides
- explain entries: auth, payee[/list/get], invoice[/list/get], bill[/list/get]

### Changed

- tipalti whoami no longer a stub; rewrites the v0.0.1 unauthenticated contract into a real probe with the same exit semantics
- tipalti learn copy expanded to cover the new verbs, env vars, and pagination model

## [0.0.1] - 2026-05-01

### Added

- Initial scaffold: `tipalti learn`, `tipalti explain`, `tipalti whoami` verbs
- afi-cli agent-first CLI structure (`cli/_errors.py`, `cli/_output.py`, `cli/_commands/`)
- CI: `tests.yml` (pytest + lint + version-check), `publish.yml` (PyPI Trusted Publishing, TestPyPI dev builds on PRs)
- Vendored skills from steward: `version-bump`, `pr-review`, `run-tests`, `gh-issues`, `pypi-maintainer`, `notebooklm`, `sonarclaude`
