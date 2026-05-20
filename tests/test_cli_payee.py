"""Tests for `tipalti payee {list,get}`."""

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


def test_payee_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payees").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"id": "p1", "refCode": "REF-1", "name": "Alice", "status": "Active"},
                    {"id": "p2", "refCode": "REF-2", "name": "Bob", "status": "Inactive"},
                ],
                "nextPageToken": "",
            },
        )
    )
    rc = main(["payee", "list", "--limit", "2"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payee list")
    assert "| id | refCode | name | status |" in out
    assert "REF-1" in out
    assert "End of results" in out


def test_payee_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payees").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [{"id": "p1"}],
                "nextPageToken": "next-tok",
            },
        )
    )
    rc = main(["payee", "list", "--limit", "1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [{"id": "p1"}]
    assert payload["next_cursor"] == "next-tok"


def test_payee_list_filter_forwarded(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    route = respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payees").mock(
        return_value=httpx.Response(200, json={"items": []})
    )
    main(["payee", "list", "--filter", "status eq 'Active'", "--json"])
    url = str(route.calls.last.request.url)
    assert "Active" in url
    assert "status" in url


def test_payee_get_404_message(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payees/missing").mock(
        return_value=httpx.Response(404, json={})
    )
    rc = main(["payee", "get", "missing"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "not found: payee missing" in err


def test_payee_get_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payees/p1").mock(
        return_value=httpx.Response(
            200, json={"id": "p1", "name": "Alice", "address": {"city": "NYC"}}
        )
    )
    rc = main(["payee", "get", "p1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# payee p1")
    assert "**id:** p1" in out
    assert "**name:** Alice" in out
    assert "## address" in out


def test_payee_list_missing_creds(capsys: pytest.CaptureFixture[str]) -> None:
    rc = main(["payee", "list"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "TIPALTI_CLIENT_ID" in err
