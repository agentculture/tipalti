"""Tests for tipalti.api.auth (token cache + acquisition)."""

from __future__ import annotations

import json
import os
import time

import httpx
import pytest
import respx

from tipalti.api._env import TipaltiEnv
from tipalti.api.auth import (
    REFRESH_WINDOW_SECONDS,
    CachedToken,
    _client_id_hash,
    cache_path,
    fetch_token,
    get_token,
    read_cached,
    write_cache,
)


def _env() -> TipaltiEnv:
    return TipaltiEnv(
        client_id="id-1",
        client_secret="secret",
        env="sandbox",
        api_base="https://api.sandbox.tipalti.com",
        token_url="https://api.sandbox.tipalti.com/oauth2/token",
    )


def test_cache_path_uses_xdg_cache_home(isolated_cache, monkeypatch: pytest.MonkeyPatch) -> None:
    path = cache_path("sandbox")
    assert str(path).startswith(str(isolated_cache))
    assert path.name == "token-sandbox.json"


def test_write_then_read_round_trip(isolated_cache) -> None:
    env = _env()
    token = CachedToken(
        access_token="tok",
        expires_at=int(time.time()) + 3600,
        env=env.env,
        client_id_hash=_client_id_hash(env.client_id),
    )
    write_cache(env, token)
    got = read_cached(env)
    assert got is not None
    assert got.access_token == "tok"


def test_cache_file_mode_is_0600(isolated_cache) -> None:
    env = _env()
    token = CachedToken("tok", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id))
    write_cache(env, token)
    mode = os.stat(cache_path(env.env)).st_mode & 0o777
    assert mode == 0o600


def test_expired_token_returns_none(isolated_cache) -> None:
    env = _env()
    expired = CachedToken("tok", int(time.time()) - 1, env.env, _client_id_hash(env.client_id))
    write_cache(env, expired)
    assert read_cached(env) is None


def test_near_expiry_returns_none(isolated_cache) -> None:
    env = _env()
    soon = CachedToken(
        "tok",
        int(time.time()) + REFRESH_WINDOW_SECONDS - 1,
        env.env,
        _client_id_hash(env.client_id),
    )
    write_cache(env, soon)
    assert read_cached(env) is None


def test_client_id_rotation_invalidates_cache(isolated_cache) -> None:
    env = _env()
    token = CachedToken("tok", int(time.time()) + 3600, env.env, _client_id_hash("OLD"))
    write_cache(env, token)
    assert read_cached(env) is None


def test_env_mismatch_invalidates_cache(isolated_cache) -> None:
    env = _env()
    token = CachedToken(
        "tok", int(time.time()) + 3600, "production", _client_id_hash(env.client_id)
    )
    # Manually put production-tagged token at the sandbox path:
    path = cache_path(env.env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "access_token": token.access_token,
                "expires_at": token.expires_at,
                "env": token.env,
                "client_id_hash": token.client_id_hash,
            }
        )
    )
    assert read_cached(env) is None


def test_corrupt_cache_returns_none(isolated_cache) -> None:
    env = _env()
    path = cache_path(env.env)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json")
    assert read_cached(env) is None


def test_missing_cache_returns_none(isolated_cache) -> None:
    assert read_cached(_env()) is None


def test_fetch_token_success(isolated_cache, respx_mock: respx.MockRouter) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "abc", "expires_in": 3600})
    )
    token = fetch_token(env)
    assert token.access_token == "abc"
    assert token.env == env.env
    assert token.expires_at > int(time.time()) + 3000


def test_fetch_token_http_error_raises(isolated_cache, respx_mock: respx.MockRouter) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(
        return_value=httpx.Response(401, json={"error": "invalid_client"})
    )
    from tipalti.cli._errors import AfiError

    with pytest.raises(AfiError) as exc:
        fetch_token(env)
    assert "auth failed" in exc.value.message


def test_get_token_uses_cache(isolated_cache, respx_mock: respx.MockRouter) -> None:
    env = _env()
    write_cache(
        env,
        CachedToken("cached", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )
    route = respx_mock.post(env.token_url)
    token = get_token(env)
    assert token.access_token == "cached"
    assert route.call_count == 0


def test_get_token_misses_cache_then_fetches_and_writes(
    isolated_cache, respx_mock: respx.MockRouter
) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "fresh", "expires_in": 1800})
    )
    token = get_token(env)
    assert token.access_token == "fresh"
    again = read_cached(env)
    assert again is not None and again.access_token == "fresh"


# ---- symlink-safe write (Qodo finding) -------------------------------------


def test_cache_write_is_symlink_safe(isolated_cache, tmp_path) -> None:
    """Pre-creating a symlink at the cache path must NOT redirect the write.

    Before the fix, ``os.open(path, O_TRUNC)`` would follow the symlink and
    truncate the linked file. After the fix, the write goes through a
    same-directory tempfile and ``os.replace``, which atomically swaps the
    symlink for the new regular file.
    """
    env = _env()
    target = tmp_path / "DO_NOT_TRUNCATE.txt"
    target.write_text("important contents")
    cache_root = cache_path(env.env)
    cache_root.parent.mkdir(parents=True, exist_ok=True)
    os.symlink(target, cache_root)

    write_cache(
        env,
        CachedToken("tok", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )

    # The linked-to file must not have been touched.
    assert target.read_text() == "important contents"
    # The cache path must now be a regular file (the symlink was atomically
    # replaced) with the token JSON.
    assert cache_root.is_file()
    assert not cache_root.is_symlink()
    payload = json.loads(cache_root.read_text())
    assert payload["access_token"] == "tok"


# ---- fetch_token robustness (Copilot finding) -------------------------------


def test_fetch_token_non_json_body_raises_afi_error(
    isolated_cache, respx_mock: respx.MockRouter
) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(return_value=httpx.Response(200, text="<html>nope</html>"))
    from tipalti.cli._errors import EXIT_USER_ERROR, AfiError

    with pytest.raises(AfiError) as exc:
        fetch_token(env)
    assert exc.value.code == EXIT_USER_ERROR
    assert "invalid token response" in exc.value.message


def test_fetch_token_missing_access_token_raises_afi_error(
    isolated_cache, respx_mock: respx.MockRouter
) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(return_value=httpx.Response(200, json={"expires_in": 3600}))
    from tipalti.cli._errors import EXIT_USER_ERROR, AfiError

    with pytest.raises(AfiError) as exc:
        fetch_token(env)
    assert exc.value.code == EXIT_USER_ERROR
    assert "invalid token response" in exc.value.message


def test_fetch_token_zero_expires_raises_afi_error(
    isolated_cache, respx_mock: respx.MockRouter
) -> None:
    env = _env()
    respx_mock.post(env.token_url).mock(
        return_value=httpx.Response(200, json={"access_token": "tok", "expires_in": 0})
    )
    from tipalti.cli._errors import EXIT_USER_ERROR, AfiError

    with pytest.raises(AfiError) as exc:
        fetch_token(env)
    assert exc.value.code == EXIT_USER_ERROR
