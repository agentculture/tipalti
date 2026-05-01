"""``tipalti invoice {list,get}`` — read-only Invoices verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli import _listing

_LIST_COLUMNS = ("id", "refCode", "payeeId", "status", "amount")


def cmd_list(args: argparse.Namespace) -> int:
    return _listing.run_list(
        args,
        noun="invoice",
        title="invoice list",
        columns=_LIST_COLUMNS,
        fetch=lambda client: client.invoices.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
    )


def cmd_get(args: argparse.Namespace) -> int:
    return _listing.run_get(
        args,
        noun="invoice",
        fetch=lambda client, rid: client.invoices.get(rid),
    )


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("invoice", help="Tipalti invoices (read-only).")
    verbs = p.add_subparsers(dest="verb")
    verbs.required = True

    p_list = verbs.add_parser("list", help="List invoices.")
    _listing.add_list_flags(p_list)
    p_list.set_defaults(func=cmd_list)

    p_get = verbs.add_parser("get", help="Get a single invoice by id.")
    _listing.add_get_flags(p_get, id_help="Invoice id.")
    p_get.set_defaults(func=cmd_get)
