# Changelog

All notable changes to this project will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/). This project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-21

### Added

- `docs/skill-sources.md` — provenance ledger mapping each vendored
  skill (`cicd`, `communicate`, `notebooklm`, `pypi-maintainer`,
  `run-tests`, `sonarclaude`, `version-bump`) to its upstream and any
  tipalti-local divergence, modeled on steward's supplier-side ledger
  but written from tipalti's downstream-consumer angle.
- `.claude/skills/cicd/scripts/_resolve-nick.sh` — nick resolver
  (first agent `suffix` in `culture.yaml`, else repo basename) so
  `pr-reply.sh` signs `- <nick> (Claude)`.

### Changed

- Resynced the vendored PR-workflow skill from steward, resolving the
  auto-broadcast issues #6/#10. The standalone `pr-review` skill is
  **renamed to `cicd`** and rebased onto `agex pr` (steward 0.12.0's
  shape): `workflow.sh` now delegates `lint` / `open` / `read` /
  `reply` / `delta` to `agex pr`, keeping the steward-origin `status`
  (SonarCloud quality gate + hotspots + unresolved-thread tally) and
  `await` (`read --wait` + `status`, non-zero exit on Sonar ERROR or
  unresolved threads) extensions. **Requires `agex`
  (`agentculture/agex-cli`) on PATH.** `STEWARD_*` env knobs are
  renamed to `TIPALTI_*` (`TIPALTI_AGEX_AGENT`, `TIPALTI_PR_AWAIT_WAIT`,
  `TIPALTI_PR_AWAIT_SECONDS`).
- `pr-reply.sh` now signs `- tipalti (Claude)` (via `_resolve-nick.sh`
  basename fallback) instead of the previous generic `- Claude`,
  matching how the `communicate` skill signs issue posts.
- `pr-status.sh` honors `SONAR_PROJECT_KEY` and points the
  full-comment-bodies footer at `agex pr read`.
- Cross-references updated `pr-review` → `cicd` in
  `communicate/SKILL.md` and `.claude/skills.local.yaml.example`.

### Removed

- `.claude/skills/cicd/scripts/pr-batch.sh` and `pr-comments.sh` —
  superseded by `agex pr reply` / `agex pr read`, mirroring steward's
  0.12.0 removal.

## [0.3.0] - 2026-05-21

### Added

- Vendored the `communicate` skill from steward
  (`.claude/skills/communicate/`) — cross-repo + mesh communication:
  `post-issue.sh` / `post-comment.sh` / `fetch-issues.sh` (thin wrappers
  around the `agtag` CLI, `agtag issue post|reply|fetch`) and
  `mesh-message.sh` (a `culture channel message` wrapper). Resolves the
  steward auto-broadcast resync brief (issue #11). Issue I/O auto-signs
  from the local `culture.yaml`, falling back to the repo basename —
  tipalti has no `culture.yaml`, so the signature resolves to
  `- tipalti (Claude)`. SKILL.md prose is identifier-adapted (consumer
  references `steward` → `tipalti`, `cicd` → `pr-review`); upstream and
  historical attributions are left intact, and the supplier-role
  broadcast section (`steward announce-skill-update`) is preserved
  verbatim since downstream vendors don't broadcast. The supplier-only
  `scripts/templates/skill-update-brief.md` is intentionally **not**
  vendored — it is consumed by steward-cli's broadcast verb (absent
  here) and documents a `../steward` sibling-checkout recipe that
  conflicts with tipalti's no-sibling-dependency rule; tipalti vendors
  only the four primitive scripts.

### Removed

- Standalone `gh-issues` skill (`.claude/skills/gh-issues/`). Its sole
  verb is superseded by `communicate`'s `fetch-issues.sh`, mirroring
  steward's 0.9.1 absorption of `gh-issues` into `communicate`.

## [0.2.0] - 2026-05-20

### Added

- tipalti payment list / payment get — read-only Payments verbs (REST v2)
- tipalti payer-entity list / payer-entity get — read-only Payer Entities verbs
- tipalti gl-account, custom-field, payment-term, tax-code — read-only list/get verbs
- explain entries (noun + list + get) for all six new nouns

### Changed

- Resource paths corrected from `/v2/...` to the documented `/api/v1/...`
- tipalti whoami now probes `/api/v1/payer-entities` (REST v2 has no identity
  endpoint); it reports reachability + auth only, with no principal payload
- learn copy expanded to cover the new nouns

### Removed

- tipalti bill list / bill get — bills are not a standalone REST v2 resource
  (they are unified under invoices); the `/v2/bills` path never existed

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
