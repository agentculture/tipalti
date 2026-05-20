"""``tipalti tax-code {list,get}`` — read-only Tax Codes verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="tax-code",
        group_help="Tipalti tax codes (read-only).",
        list_help="List tax codes.",
        list_columns=("id", "name", "rate"),
        get_help="Get a single tax code by id.",
        get_id_help="Tax code id.",
        list_fetch=lambda client, args: client.tax_codes.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.tax_codes.get(rid),
    )
