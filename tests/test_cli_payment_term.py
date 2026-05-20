"""Tests for `tipalti payment-term {list,get}`."""

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


def test_payment_term_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "t1", "name": "Net 30", "days": 30}]}
        )
    )
    rc = main(["payment-term", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payment-term list")
    assert "| id | name | days |" in out
    assert "Net 30" in out


def test_payment_term_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "t1"}]})
    )
    rc = main(["payment-term", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "t1"}]


def test_payment_term_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "name": "Net 30"})
    )
    rc = main(["payment-term", "get", "t1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# payment-term t1")
