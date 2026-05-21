# Skill sources — vendored-skill provenance

`tipalti` is a **downstream consumer** of the AgentCulture skill mesh. Every
skill under `.claude/skills/` is a vendored copy of an upstream canonical
skill (mostly owned by [`steward`](https://github.com/agentculture/steward),
the skill supplier). Nothing is imported across repos at runtime — this is
the **cite, don't import** pattern: tipalti owns its copy and may diverge
from upstream, recording the divergence here and in the skill's own
`SKILL.md` frontmatter.

This file is the deterministic upstream map for re-syncing. When an upstream
skill changes, tipalti's copy does **not** auto-update; re-sync explicitly
(today: manual; the planned `steward doctor --apply` will consult this map).

| Skill | Upstream | Vendored as | Notes / local divergence |
|-------|----------|-------------|--------------------------|
| `cicd` | `steward` (`.claude/skills/cicd/`) — layered on `agex pr` (in `agentculture/agex-cli`) | `cicd` (renamed from `pr-review` in tipalti 0.4.0) | Thin delegate to `agex pr` for lint / open / read / reply / delta, plus two steward-origin extensions: `status` (SonarCloud quality gate + hotspots + unresolved-thread tally + deploy-preview URL) and `await` (composes `agex pr read --wait` with `status`, exits non-zero on Sonar ERROR / unresolved threads). Both filed upstream as [agex-cli#41](https://github.com/agentculture/agex-cli/issues/41). Local divergence: `STEWARD_*` env knobs renamed to `TIPALTI_*`; the dead Cloudflare-Pages deploy-preview probe in `pr-status.sh` is kept verbatim but inert (tipalti ships no Pages site). Replaced tipalti's pre-0.12.0 standalone `pr-review` copy. |
| `communicate` | `steward` (`.claude/skills/communicate/`) | `communicate` | Cross-repo + mesh communication: file / comment on / fetch issues on sibling repos (auto-signed) and send live Culture mesh messages (unsigned). Issue I/O backed by `agtag` (>=0.1); signature resolves from the local `culture.yaml`, falling back to the repo basename — tipalti has no `culture.yaml`, so it signs `- tipalti (Claude)`. The supplier-only broadcast template is intentionally not vendored (tipalti consumes, it does not broadcast). |
| `notebooklm` | `steward` (`.claude/skills/notebooklm/`) | `notebooklm` | Generates GitHub blob URLs for repo docs; auto-detects branch + remote. Vendored verbatim. |
| `pypi-maintainer` | `steward` (`.claude/skills/pypi-maintainer/`) | `pypi-maintainer` | Switches a PyPI package install between pypi / test-pypi / local. Vendored verbatim. |
| `run-tests` | `steward` (`.claude/skills/run-tests/`) | `run-tests` | Coverage source resolves from `[tool.coverage.run]` in `pyproject.toml`; portable without modification. |
| `sonarclaude` | `steward` (`.claude/skills/sonarclaude/`) | `sonarclaude` | SonarCloud API client. Project key resolves from `$SONAR_PROJECT` or `--project KEY`. |
| `version-bump` | `steward` (`.claude/skills/version-bump/`) | `version-bump` | Pure Python; prepends a Keep-a-Changelog entry. Required on every PR (the `version-check` CI job blocks merge otherwise). |

## Re-sync policy

- **Cite, don't import.** Skills are copied in, not symlinked or installed.
  tipalti owns and may modify its copy.
- **Re-sync explicitly.** Upstream changes do not auto-propagate. Steward
  files an auto-broadcast issue against tipalti when an upstream skill moves
  on (e.g. issues #6 / #10 drove the 0.4.0 `cicd` resync).
- **Diverge intentionally.** Record any tipalti-specific divergence both in
  the table above and in the skill's `SKILL.md` frontmatter `description`.
- **No external path dependencies.** Per the project skills 3-rule contract,
  scripts must not reach into another skill's home-directory copy or any
  location outside this repo. `steward doctor . --scope self` enforces this.
