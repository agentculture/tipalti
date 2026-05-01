"""Environment-variable resolution for the Tipalti REST v2 client.

The CLI reads three required and two optional env vars:

* ``TIPALTI_CLIENT_ID``   — OAuth2 client ID (required)
* ``TIPALTI_CLIENT_SECRET`` — OAuth2 client secret (required)
* ``TIPALTI_ENV``         — ``sandbox`` | ``production``; default ``sandbox``
* ``TIPALTI_API_BASE``    — override the default API base URL for the env
* ``TIPALTI_TOKEN_URL``   — override the default OAuth2 token URL for the env

The default base URLs match Tipalti's documented hosts; the override env
vars exist so deployers can correct them at runtime without code changes
(the spec fixes the *shape*, not the URL strings).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from tipalti.cli._errors import EXIT_ENV_ERROR, AfiError

VALID_ENVS = ("sandbox", "production")
DEFAULT_ENV = "sandbox"

_DEFAULT_API_BASE: dict[str, str] = {
    "sandbox": "https://api.sandbox.tipalti.com",
    "production": "https://api.tipalti.com",
}
_DEFAULT_TOKEN_URL: dict[str, str] = {
    "sandbox": "https://api.sandbox.tipalti.com/oauth2/token",
    "production": "https://api.tipalti.com/oauth2/token",
}


@dataclass(frozen=True)
class TipaltiEnv:
    """Resolved Tipalti environment + credentials."""

    client_id: str
    client_secret: str
    env: str
    api_base: str
    token_url: str


def load_env(source: Mapping[str, str] | None = None) -> TipaltiEnv:
    """Read env vars and return a :class:`TipaltiEnv`.

    ``source`` defaults to ``os.environ``; tests pass an explicit mapping.
    Raises :class:`AfiError` with ``EXIT_ENV_ERROR`` for missing creds or
    unknown ``TIPALTI_ENV`` values.
    """
    env_map = source if source is not None else os.environ

    env_name = (env_map.get("TIPALTI_ENV") or DEFAULT_ENV).strip().lower()
    if env_name not in VALID_ENVS:
        raise AfiError(
            code=EXIT_ENV_ERROR,
            message=f"unknown TIPALTI_ENV: {env_name!r}",
            remediation=f"use one of: {', '.join(VALID_ENVS)}",
        )

    client_id = (env_map.get("TIPALTI_CLIENT_ID") or "").strip()
    client_secret = (env_map.get("TIPALTI_CLIENT_SECRET") or "").strip()
    if not client_id or not client_secret:
        raise AfiError(
            code=EXIT_ENV_ERROR,
            message="missing TIPALTI_CLIENT_ID/SECRET",
            remediation="set env vars; see 'tipalti explain auth'",
            kind="missing_creds",
        )

    api_base = (env_map.get("TIPALTI_API_BASE") or _DEFAULT_API_BASE[env_name]).rstrip("/")
    token_url = env_map.get("TIPALTI_TOKEN_URL") or _DEFAULT_TOKEN_URL[env_name]

    return TipaltiEnv(
        client_id=client_id,
        client_secret=client_secret,
        env=env_name,
        api_base=api_base,
        token_url=token_url,
    )
