"""``tipalti bill {list,get}`` — read-only Bills verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="bill",
        group_help="Tipalti bills (read-only).",
        list_help="List bills.",
        list_columns=("id", "refCode", "payeeId", "status", "amount"),
        get_help="Get a single bill by id.",
        get_id_help="Bill id.",
        list_fetch=lambda client, args: client.bills.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.bills.get(rid),
    )
