# tipalti

CLI for Tipalti Solutions — scaffolded from the AgentCulture sibling pattern.
Read-only explorer over Tipalti REST v2 (Payees, Invoices, Bills) plus the
agent-first affordances (`learn`, `explain`, `whoami`).

The first resident user of this CLI is an LLM agent. Every verb supports
`--json`, default human-mode output is markdown, errors carry
machine-readable remediation hints, and one verb invocation = one upstream
HTTP request.

## Install

```bash
uv tool install tipalti
# or
pipx install tipalti
```

## Quickstart — agent-first affordances

```bash
tipalti --version           # 0.1.0
tipalti learn               # structured self-teaching prompt for agents
tipalti learn --json        # machine-readable form
tipalti explain tipalti     # root markdown doc
tipalti explain auth        # env-var setup
tipalti explain payee       # docs for the payee noun group
```

## Quickstart — Tipalti REST v2 (read-only)

```bash
export TIPALTI_CLIENT_ID=...
export TIPALTI_CLIENT_SECRET=...
export TIPALTI_ENV=sandbox        # or production (default: sandbox)

tipalti whoami                                       # markdown principal block
tipalti whoami --json                                # JSON envelope

tipalti payee list --limit 25                        # markdown table
tipalti payee list --filter "status eq 'Active'"     # raw $filter passthrough
tipalti payee list --json --cursor <token>           # paginate by cursor
tipalti payee get <id>                               # markdown record
tipalti payee get <id> --json                        # raw API record

tipalti invoice list --limit 25
tipalti invoice get <id>
tipalti bill list --limit 25
tipalti bill get <id>
```

Bearer tokens are cached at `$XDG_CACHE_HOME/tipalti/token-<env>.json`
(file mode `0600`). Delete the file to force re-auth.

## Status

Pre-1.0. v0.1.0 ships read-only verbs over Tipalti REST v2's Payees,
Invoices, and Bills resources, plus the agent-first affordances and a
real `whoami` probe. Mutations, iFrame URL generation, webhooks, SOAP,
tax forms, and KYC land in later releases.

## Development

```bash
uv sync
uv run pytest -n auto -v
uv run tipalti --version
```

See [`CLAUDE.md`](CLAUDE.md) for the full project shape, conventions, and
publish flow. The repo follows the AgentCulture sibling pattern — see
[`agentculture/steward`](https://github.com/agentculture/steward) and
[`agentculture/afi-cli`](https://github.com/agentculture/afi-cli) for the
canonical templates.

## License

MIT — see [`LICENSE`](LICENSE).
