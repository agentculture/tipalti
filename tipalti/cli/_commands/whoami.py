"""``tipalti whoami`` — auth probe stub (Tipalti-specific).

Returns ``unauthenticated`` until real Tipalti API auth lands. Supports
``--json``. Exit code is always ``0`` (probe, not gate).
"""

from __future__ import annotations

import argparse

from tipalti.cli._output import emit_result


def cmd_whoami(args: argparse.Namespace) -> int:
    payload: dict[str, object] = {"status": "unauthenticated", "principal": None}
    if getattr(args, "json", False):
        emit_result(payload, json_mode=True)
    else:
        emit_result("unauthenticated", json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "whoami",
        help="Print the active Tipalti principal (stub in v0.0.1).",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_whoami)
