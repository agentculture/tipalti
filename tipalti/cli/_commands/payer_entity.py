"""``tipalti payer-entity {list,get}`` — read-only Payer Entities verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payer-entity",
        group_help="Tipalti payer entities (read-only).",
        list_help="List payer entities.",
        list_columns=("id", "name", "status"),
        get_help="Get a single payer entity by id.",
        get_id_help="Payer entity id.",
        list_fetch=lambda client, args: client.payer_entities.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payer_entities.get(rid),
    )
