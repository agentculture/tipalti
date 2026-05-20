"""Shared pytest fixtures.

Most tests must run with no Tipalti env vars present (so they don't pick
up real credentials from the developer's shell). The ``clean_env``
autouse fixture strips every ``TIPALTI_*`` var before each test; tests
that need credentials set them explicitly via ``monkeypatch.setenv``.
"""

from __future__ import annotations

import time

import pytest

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache


@pytest.fixture(autouse=True)
def clean_tipalti_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "TIPALTI_CLIENT_ID",
        "TIPALTI_CLIENT_SECRET",
        "TIPALTI_ENV",
        "TIPALTI_API_BASE",
        "TIPALTI_TOKEN_URL",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def isolated_cache(monkeypatch: pytest.MonkeyPatch, tmp_path):
    """Point the token cache at a tmp dir."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    return tmp_path


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    """Prime credentials + a fresh cached token so CLI tests skip the token call."""
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )
