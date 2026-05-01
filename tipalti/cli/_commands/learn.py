"""``tipalti learn`` — the learnability affordance (shape-adapt)."""

from __future__ import annotations

import argparse

from tipalti import __version__
from tipalti.cli._output import emit_result

_TEXT = """\
tipalti — CLI for Tipalti Solutions.

Purpose
-------
tipalti is a command-line interface for working with Tipalti Solutions.
The v0.0.1 surface ships only the agent-first affordances (`learn`,
`explain`) and an auth-probe stub (`whoami`); domain verbs that talk to
the Tipalti API land in subsequent releases.

Commands
--------
  tipalti learn              Print this self-teaching prompt. Supports --json.
  tipalti explain <path>...  Print markdown docs for any noun/verb path.
                              Supports --json.
  tipalti whoami             Print the active Tipalti principal. Stub for
                              now (always reports "unauthenticated") until
                              real Tipalti API auth is wired. Supports --json.

Machine-readable output
-----------------------
Every command that produces a listing or report supports --json. Errors in
JSON mode emit {"code", "message", "remediation"} to stderr. Stdout and
stderr are never mixed.

Exit-code policy
----------------
  0 success
  1 user-input error (bad flag, bad path, missing arg)
  2 environment / setup error
  3+ reserved

More detail
-----------
  tipalti explain tipalti
"""


def _as_json_payload() -> dict[str, object]:
    return {
        "tool": "tipalti",
        "version": __version__,
        "purpose": "CLI for Tipalti Solutions.",
        "commands": [
            {"path": ["learn"], "summary": "Self-teaching prompt."},
            {"path": ["explain"], "summary": "Markdown docs by path."},
            {"path": ["whoami"], "summary": "Auth probe (stub in v0.0.1)."},
        ],
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
