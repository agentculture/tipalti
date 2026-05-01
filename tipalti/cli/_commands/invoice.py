"""``tipalti invoice {list,get}`` — read-only Invoices verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="invoice",
        group_help="Tipalti invoices (read-only).",
        list_help="List invoices.",
        list_columns=("id", "refCode", "payeeId", "status", "amount"),
        get_help="Get a single invoice by id.",
        get_id_help="Invoice id.",
        list_fetch=lambda client, args: client.invoices.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.invoices.get(rid),
    )
