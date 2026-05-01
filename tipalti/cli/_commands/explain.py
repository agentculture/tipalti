"""``tipalti explain <path>...`` — global markdown catalog lookup (stable-contract).

``explain`` is global (not nested under a noun). It takes zero or more path
tokens and resolves them via the catalog in :mod:`tipalti.explain`.
Unknown paths raise :class:`AfiError` with a remediation hint.
"""

from __future__ import annotations

import argparse

from tipalti.cli._output import emit_result
from tipalti.explain import resolve


def cmd_explain(args: argparse.Namespace) -> int:
    path = tuple(args.path) if args.path else ()
    markdown = resolve(path)
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result({"path": list(path), "markdown": markdown}, json_mode=True)
    else:
        emit_result(markdown, json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "explain",
        help="Print markdown docs for a noun/verb path (e.g. 'tipalti explain cli foo').",
    )
    p.add_argument(
        "path",
        nargs="*",
        help="Command path tokens; empty = root (same as 'tipalti').",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_explain)
