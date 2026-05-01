# tipalti

CLI for Tipalti Solutions — scaffolded from the AgentCulture sibling pattern.

## Install

```bash
uv tool install tipalti
# or
pipx install tipalti
```

## Quickstart

```bash
tipalti --version           # 0.0.1
tipalti learn               # structured self-teaching prompt for agents
tipalti learn --json        # machine-readable form
tipalti explain tipalti     # root markdown doc
tipalti explain whoami      # docs for the whoami verb
tipalti whoami              # auth probe (v0.0.1: always "unauthenticated")
```

## Status

Pre-1.0. v0.0.1 ships only the agent-first affordances (`learn`, `explain`)
and an auth-probe stub (`whoami`). Domain verbs that exercise the Tipalti
API land in later releases.

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
