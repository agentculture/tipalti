"""Tests for `tipalti whoami` (real auth probe)."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


def _prime_token() -> None:
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_whoami_unauthenticated_no_env(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["whoami"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "unauthenticated" in out
    assert out.startswith("# tipalti whoami")


def test_whoami_unauthenticated_no_env_json(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["whoami", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unauthenticated"
    assert payload["principal"] is None
    assert payload["env"] is None


def test_whoami_401_is_unauthenticated_exit_zero(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cache,
    capsys: pytest.CaptureFixture[str],
    respx_mock: respx.MockRouter,
) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "s")
    _prime_token()
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(401, json={})
    )
    rc = main(["whoami", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unauthenticated"
    assert payload["env"] == "sandbox"


def test_whoami_authenticated_markdown(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cache,
    capsys: pytest.CaptureFixture[str],
    respx_mock: respx.MockRouter,
) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "s")
    _prime_token()
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "e1"}]})
    )
    rc = main(["whoami"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "authenticated" in out
    assert "**env:** sandbox" in out


def test_whoami_unknown_env_propagates_error(
    monkeypatch: pytest.MonkeyPatch,
    isolated_cache,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """An unknown TIPALTI_ENV must NOT be swallowed as 'unauthenticated'."""
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "s")
    monkeypatch.setenv("TIPALTI_ENV", "staging")  # not in VALID_ENVS
    rc = main(["whoami"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "unknown TIPALTI_ENV" in err
    assert "staging" in err
