"""``tipalti gl-account {list,get}`` — read-only GL Accounts verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="gl-account",
        group_help="Tipalti GL accounts (read-only).",
        list_help="List GL accounts.",
        list_columns=("id", "name", "code"),
        get_help="Get a single GL account by id.",
        get_id_help="GL account id.",
        list_fetch=lambda client, args: client.gl_accounts.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.gl_accounts.get(rid),
    )
