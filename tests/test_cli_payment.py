"""Tests for `tipalti payment {list,get}`."""

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


def test_payment_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"id": "PMT-1", "refCode": "R1", "status": "Paid",
                     "amount": "100", "currency": "USD"},
                ],
                "nextPageToken": "",
            },
        )
    )
    rc = main(["payment", "list", "--limit", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payment list")
    assert "| id | refCode | status | amount | currency |" in out
    assert "PMT-1" in out


def test_payment_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "PMT-1"}], "nextPageToken": "t"})
    )
    rc = main(["payment", "list", "--limit", "1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [{"id": "PMT-1"}]
    assert payload["next_cursor"] == "t"


def test_payment_get_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments/PMT-1").mock(
        return_value=httpx.Response(200, json={"id": "PMT-1", "status": "Paid"})
    )
    rc = main(["payment", "get", "PMT-1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# payment PMT-1")
    assert "**id:** PMT-1" in out


def test_payment_get_404(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments/missing").mock(
        return_value=httpx.Response(404, json={})
    )
    rc = main(["payment", "get", "missing"])
    assert rc == 1
    assert "not found: payment missing" in capsys.readouterr().err
