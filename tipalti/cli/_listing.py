"""Shared helpers for the noun-group ``list`` / ``get`` verbs.

Each noun-group module (``payee.py``, ``invoice.py``, ``bill.py``) wires
its argparse subparsers to handlers in this module. The actual API call
is supplied as a callable so each noun can target its own resource.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING, Any, Callable, Sequence

from tipalti.cli._output import (
    emit_result,
    render_list_md,
    render_record_md,
)

if TYPE_CHECKING:
    from tipalti.api import TipaltiClient

_LIMIT_HELP = "Maximum records to return (default 100, max 500)."
_CURSOR_HELP = "Continuation token from a previous list response."
_FILTER_HELP = "Server-side filter, forwarded raw as $filter (e.g. \"status eq 'Active'\")."


def add_list_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", type=int, default=100, help=_LIMIT_HELP)
    parser.add_argument("--cursor", default=None, help=_CURSOR_HELP)
    parser.add_argument("--filter", dest="filter", default=None, help=_FILTER_HELP)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")


def add_get_flags(parser: argparse.ArgumentParser, *, id_help: str) -> None:
    parser.add_argument("id", help=id_help)
    parser.add_argument("--json", action="store_true", help="Emit structured JSON.")


def run_list(
    args: argparse.Namespace,
    *,
    noun: str,
    title: str,
    columns: Sequence[str],
    fetch: Callable[["TipaltiClient"], dict[str, Any]],
) -> int:
    from tipalti.api import TipaltiClient

    json_mode = bool(getattr(args, "json", False))
    with TipaltiClient.from_env() as client:
        envelope = fetch(client)

    if json_mode:
        emit_result(envelope, json_mode=True)
        return 0

    next_command = f"tipalti {noun} list"
    markdown = render_list_md(
        title,
        envelope.get("items", []),
        columns,
        next_cursor=envelope.get("next_cursor"),
        next_command=next_command,
    )
    emit_result(markdown, json_mode=False)
    return 0


def run_get(
    args: argparse.Namespace,
    *,
    noun: str,
    fetch: Callable[["TipaltiClient", str], Any],
) -> int:
    from tipalti.api import TipaltiClient

    json_mode = bool(getattr(args, "json", False))
    resource_id = args.id
    with TipaltiClient.from_env() as client:
        record = fetch(client, resource_id)

    if json_mode:
        emit_result(record, json_mode=True)
        return 0

    title = f"{noun} {resource_id}"
    emit_result(render_record_md(title, record), json_mode=False)
    return 0
