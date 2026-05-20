"""``tipalti payment {list,get}`` — read-only Payments verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payment",
        group_help="Tipalti payments (read-only).",
        list_help="List payments.",
        list_columns=("id", "refCode", "status", "amount", "currency"),
        get_help="Get a single payment by id.",
        get_id_help="Payment id (or refCode, depending on tenant).",
        list_fetch=lambda client, args: client.payments.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payments.get(rid),
    )
