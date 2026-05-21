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
through their REST v2 API. v0.2.0 ships a read-only explorer over the
Payees, Invoices, Payments, Payer Entities, GL Accounts, Custom Fields,
Payment Terms, and Tax Codes resources, plus the agent-first affordances
(`learn`, `explain`) and a real auth probe (`whoami`).

The first resident user of this CLI is an LLM agent. Every verb supports
`--json`, exit codes are stable, errors include machine-readable
remediation hints, and one verb invocation = one upstream HTTP request.

Commands
--------
  tipalti learn              Print this self-teaching prompt. Supports --json.
  tipalti explain <path>...  Print markdown docs for any noun/verb path.
                             Supports --json.
  tipalti whoami             Probe auth reachability. Supports --json. Reports
                             `unauthenticated` and exits 0 when no credentials
                             are configured (probe, not gate). REST v2 has no
                             identity endpoint, so no principal is returned.

  tipalti payee list         List payees. Flags: --limit, --cursor, --filter,
                             --json. One HTTP request per call.
  tipalti payee get <id>     Fetch a single payee. Supports --json.
  tipalti invoice list       List invoices. Same flag set as `payee list`.
  tipalti invoice get <id>   Fetch a single invoice. Supports --json.
  tipalti payment list       List payments. Same flag set as `payee list`.
  tipalti payment get <id>   Fetch a single payment. Supports --json.
  tipalti payer-entity list  List payer entities. Same flag set as `payee list`.
  tipalti payer-entity get <id>
                             Fetch a single payer entity. Supports --json.
  tipalti gl-account list    List GL accounts. Same flag set as `payee list`.
  tipalti gl-account get <id>
                             Fetch a single GL account. Supports --json.
  tipalti custom-field list  List custom fields. Same flag set as `payee list`.
  tipalti custom-field get <id>
                             Fetch a single custom field. Supports --json.
  tipalti payment-term list  List payment terms. Same flag set as `payee list`.
  tipalti payment-term get <id>
                             Fetch a single payment term. Supports --json.
  tipalti tax-code list      List tax codes. Same flag set as `payee list`.
  tipalti tax-code get <id>  Fetch a single tax code. Supports --json.

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
        "purpose": (
            "Read-only CLI explorer for Tipalti REST v2 "
            "(payees, invoices, payments, and reference data)."
        ),
        "primary_consumer": "LLM agent",
        "commands": [
            {"path": ["learn"], "summary": "Self-teaching prompt."},
            {"path": ["explain"], "summary": "Markdown docs by path."},
            {"path": ["whoami"], "summary": "Auth probe; exit 0 even when unauth."},
            {"path": ["payee", "list"], "summary": "List payees."},
            {"path": ["payee", "get"], "summary": "Get a single payee."},
            {"path": ["invoice", "list"], "summary": "List invoices."},
            {"path": ["invoice", "get"], "summary": "Get a single invoice."},
            {"path": ["payment", "list"], "summary": "List payments."},
            {"path": ["payment", "get"], "summary": "Get a single payment."},
            {"path": ["payer-entity", "list"], "summary": "List payer entities."},
            {"path": ["payer-entity", "get"], "summary": "Get a single payer entity."},
            {"path": ["gl-account", "list"], "summary": "List GL accounts."},
            {"path": ["gl-account", "get"], "summary": "Get a single GL account."},
            {"path": ["custom-field", "list"], "summary": "List custom fields."},
            {"path": ["custom-field", "get"], "summary": "Get a single custom field."},
            {"path": ["payment-term", "list"], "summary": "List payment terms."},
            {"path": ["payment-term", "get"], "summary": "Get a single payment term."},
            {"path": ["tax-code", "list"], "summary": "List tax codes."},
            {"path": ["tax-code", "get"], "summary": "Get a single tax code."},
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
