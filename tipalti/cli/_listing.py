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


def register_noun_group(
    sub: argparse._SubParsersAction,
    *,
    noun: str,
    group_help: str,
    list_help: str,
    list_columns: Sequence[str],
    get_help: str,
    get_id_help: str,
    list_fetch: Callable[["TipaltiClient", argparse.Namespace], dict[str, Any]],
    get_fetch: Callable[["TipaltiClient", str], Any],
) -> None:
    """Register a noun group's ``list`` and ``get`` verbs.

    The noun module supplies just the resource-shaped bits (columns, fetch
    callables, help strings); this helper owns the argparse boilerplate
    and the dispatch glue. Keeps each noun module short, makes it
    impossible to drift the verb surface across nouns.
    """
    parser = sub.add_parser(noun, help=group_help)
    verbs = parser.add_subparsers(dest="verb")
    verbs.required = True

    list_parser = verbs.add_parser("list", help=list_help)
    add_list_flags(list_parser)

    def _cmd_list(args: argparse.Namespace) -> int:
        return run_list(
            args,
            noun=noun,
            title=f"{noun} list",
            columns=list_columns,
            fetch=lambda client: list_fetch(client, args),
        )

    list_parser.set_defaults(func=_cmd_list)

    get_parser = verbs.add_parser("get", help=get_help)
    add_get_flags(get_parser, id_help=get_id_help)

    def _cmd_get(args: argparse.Namespace) -> int:
        return run_get(args, noun=noun, fetch=get_fetch)

    get_parser.set_defaults(func=_cmd_get)
