"""Tests for `tipalti invoice {list,get}` (mirrors test_cli_payee shape)."""

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


def test_invoice_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/invoices").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "inv-1", "status": "Approved"}]})
    )
    rc = main(["invoice", "list", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"][0]["id"] == "inv-1"


def test_invoice_get_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/invoices/inv-1").mock(
        return_value=httpx.Response(200, json={"id": "inv-1", "amount": 100, "status": "Approved"})
    )
    rc = main(["invoice", "get", "inv-1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# invoice inv-1")
    assert "**amount:** `100`" in out


def test_invoice_list_next_cursor_footer(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/invoices").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"id": f"i{n}"} for n in range(2)],
                "nextPageToken": "tok-next",
            },
        )
    )
    rc = main(["invoice", "list", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "Next page:" in out
    assert "tipalti invoice list --cursor=tok-next" in out
