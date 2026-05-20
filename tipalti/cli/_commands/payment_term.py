"""``tipalti payment-term {list,get}`` — read-only Payment Terms verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payment-term",
        group_help="Tipalti payment terms (read-only).",
        list_help="List payment terms.",
        list_columns=("id", "name", "days"),
        get_help="Get a single payment term by id.",
        get_id_help="Payment term id.",
        list_fetch=lambda client, args: client.payment_terms.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payment_terms.get(rid),
    )
