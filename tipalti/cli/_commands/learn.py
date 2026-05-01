"""``tipalti learn`` — the learnability affordance (shape-adapt)."""

from __future__ import annotations

import argparse

from tipalti import __version__
from tipalti.cli._output import emit_result

_TEXT = """\
tipalti — CLI for Tipalti Solutions.

Purpose
-------
tipalti is a command-line interface for working with Tipalti Solutions
through their REST v2 API. v0.1.0 ships a read-only explorer over the
Payees, Invoices, and Bills resources, plus the agent-first affordances
(`learn`, `explain`) and a real auth probe (`whoami`).

The first resident user of this CLI is an LLM agent. Every verb supports
`--json`, exit codes are stable, errors include machine-readable
remediation hints, and one verb invocation = one upstream HTTP request.

Commands
--------
  tipalti learn              Print this self-teaching prompt. Supports --json.
  tipalti explain <path>...  Print markdown docs for any noun/verb path.
                             Supports --json.
  tipalti whoami             Probe the active Tipalti principal. Supports --json.
                             Reports `unauthenticated` and exits 0 when no
                             credentials are configured (probe, not gate).

  tipalti payee list         List payees. Flags: --limit, --cursor, --filter,
                             --json. One HTTP request per call.
  tipalti payee get <id>     Fetch a single payee. Supports --json.
  tipalti invoice list       List invoices. Same flag set as `payee list`.
  tipalti invoice get <id>   Fetch a single invoice. Supports --json.
  tipalti bill list          List bills. Same flag set as `payee list`.
  tipalti bill get <id>      Fetch a single bill. Supports --json.

Authentication (env vars)
-------------------------
  TIPALTI_CLIENT_ID, TIPALTI_CLIENT_SECRET   OAuth2 client credentials.
  TIPALTI_ENV=sandbox|production             Environment (default: sandbox).
  TIPALTI_API_BASE                           Optional base-URL override.
  TIPALTI_TOKEN_URL                          Optional token-URL override.

Tokens are cached at $XDG_CACHE_HOME/tipalti/token-<env>.json (mode 0600);
delete the file to force re-auth.

Pagination & filtering
----------------------
List verbs make exactly one HTTP request per invocation. Each response
carries an envelope `{"items": [...], "next_cursor": str|null}` (in JSON
mode); in human (markdown) mode, the same continuation token shows up in
a footer line. There is no `--all` auto-follow flag in this release.

`--filter STR` is forwarded raw as the OData `$filter` query parameter.
The CLI does no client-side validation; the API rejects bad input.

Machine-readable output
-----------------------
Every command supports --json. Default human mode is markdown (heading +
key/value list or table) so coder agents can read it cleanly. Errors in
JSON mode emit {"code", "message", "remediation"} to stderr. Stdout and
stderr are never mixed.

Exit-code policy
----------------
  0 success
  1 user-input error (bad flag, bad path, missing arg, API 4xx)
  2 environment / setup error (missing env vars, transport failure)
  3+ reserved

More detail
-----------
  tipalti explain tipalti
  tipalti explain auth
  tipalti explain payee
"""


def _as_json_payload() -> dict[str, object]:
    return {
        "tool": "tipalti",
        "version": __version__,
        "purpose": "Read-only CLI explorer for Tipalti REST v2 (Payees, Invoices, Bills).",
        "primary_consumer": "LLM agent",
        "commands": [
            {"path": ["learn"], "summary": "Self-teaching prompt."},
            {"path": ["explain"], "summary": "Markdown docs by path."},
            {"path": ["whoami"], "summary": "Auth probe; exit 0 even when unauth."},
            {"path": ["payee", "list"], "summary": "List payees."},
            {"path": ["payee", "get"], "summary": "Get a single payee."},
            {"path": ["invoice", "list"], "summary": "List invoices."},
            {"path": ["invoice", "get"], "summary": "Get a single invoice."},
            {"path": ["bill", "list"], "summary": "List bills."},
            {"path": ["bill", "get"], "summary": "Get a single bill."},
        ],
        "env_vars": {
            "TIPALTI_CLIENT_ID": "OAuth2 client ID (required)",
            "TIPALTI_CLIENT_SECRET": "OAuth2 client secret (required)",  # nosec B105
            "TIPALTI_ENV": "sandbox | production (default: sandbox)",
            "TIPALTI_API_BASE": "optional base-URL override",
            "TIPALTI_TOKEN_URL": "optional token-URL override",  # nosec B105
        },
        "list_envelope": {"items": "list of records", "next_cursor": "str | null"},
        "exit_codes": {
            "0": "success",
            "1": "user-input error",
            "2": "environment/setup error",
        },
        "json_support": True,
        "explain_pointer": "tipalti explain <path>",
    }


def cmd_learn(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        emit_result(_as_json_payload(), json_mode=True)
    else:
        emit_result(_TEXT, json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "learn",
        help="Print a structured self-teaching prompt for agent consumers.",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_learn)
