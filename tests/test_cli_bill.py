"""Tests for `tipalti bill {list,get}` (mirrors test_cli_payee shape)."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_bill_list_empty(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/bills").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    rc = main(["bill", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "No results" in out


def test_bill_get_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/bills/B-1").mock(
        return_value=httpx.Response(200, json={"id": "B-1", "status": "Open"})
    )
    rc = main(["bill", "get", "B-1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"id": "B-1", "status": "Open"}
