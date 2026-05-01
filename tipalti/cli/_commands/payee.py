"""``tipalti payee {list,get}`` — read-only Payees verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payee",
        group_help="Tipalti payees (read-only).",
        list_help="List payees.",
        list_columns=("id", "refCode", "name", "status"),
        get_help="Get a single payee by id.",
        get_id_help="Payee id (or refCode, depending on tenant).",
        list_fetch=lambda client, args: client.payees.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payees.get(rid),
    )
