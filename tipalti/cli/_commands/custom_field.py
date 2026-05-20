"""``tipalti custom-field {list,get}`` — read-only Custom Fields verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="custom-field",
        group_help="Tipalti custom fields (read-only).",
        list_help="List custom fields.",
        list_columns=("id", "name", "type"),
        get_help="Get a single custom field by id.",
        get_id_help="Custom field id.",
        list_fetch=lambda client, args: client.custom_fields.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.custom_fields.get(rid),
    )
