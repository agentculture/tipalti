"""Tests for `tipalti payer-entity {list,get}`."""

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


def test_payer_entity_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "e1", "name": "Entity One", "status": "Active"}]}
        )
    )
    rc = main(["payer-entity", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payer-entity list")
    assert "| id | name | status |" in out
    assert "Entity One" in out


def test_payer_entity_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "e1"}], "nextPageToken": "t"})
    )
    rc = main(["payer-entity", "list", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [{"id": "e1"}]


def test_payer_entity_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities/e1").mock(
        return_value=httpx.Response(200, json={"id": "e1", "name": "Entity One"})
    )
    rc = main(["payer-entity", "get", "e1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# payer-entity e1")
    assert "**name:** Entity One" in out
