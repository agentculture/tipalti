"""``tipalti whoami`` — auth probe.

Probe, not gate: missing creds and 401 both report ``unauthenticated`` and
exit 0. Other API/transport errors — including unknown ``TIPALTI_ENV`` —
propagate (`EXIT_ENV_ERROR` / `EXIT_USER_ERROR`).
"""

from __future__ import annotations

import argparse

from tipalti.cli._errors import AfiError
from tipalti.cli._output import emit_result, render_kv_md


def _emit_unauthenticated(json_mode: bool, env: str | None) -> int:
    payload = {"status": "unauthenticated", "principal": None, "env": env}
    if json_mode:
        emit_result(payload, json_mode=True)
    else:
        emit_result(
            render_kv_md("tipalti whoami", {"status": "unauthenticated", "env": env}),
            json_mode=False,
        )
    return 0


def cmd_whoami(args: argparse.Namespace) -> int:
    from tipalti.api import TipaltiClient, load_env

    json_mode = bool(getattr(args, "json", False))
    try:
        env = load_env()
    except AfiError as err:
        if err.kind == "missing_creds":
            return _emit_unauthenticated(json_mode, env=None)
        raise

    with TipaltiClient(env) as client:
        result = client.whoami()

    if json_mode:
        emit_result(result, json_mode=True)
        return 0

    if result["status"] == "unauthenticated":
        return _emit_unauthenticated(json_mode=False, env=result.get("env"))

    fields: dict[str, object] = {"status": "authenticated", "env": result.get("env")}
    emit_result(render_kv_md("tipalti whoami", fields), json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "whoami",
        help="Probe Tipalti auth reachability (no identity payload; exit 0 even when unauth).",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_whoami)
