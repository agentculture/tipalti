"""Tests for `tipalti tax-code {list,get}`."""

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


def test_tax_code_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "x1", "name": "VAT", "rate": "0.20"}]}
        )
    )
    rc = main(["tax-code", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## tax-code list")
    assert "| id | name | rate |" in out
    assert "VAT" in out


def test_tax_code_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "x1"}]})
    )
    rc = main(["tax-code", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "x1"}]


def test_tax_code_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes/x1").mock(
        return_value=httpx.Response(200, json={"id": "x1", "name": "VAT"})
    )
    rc = main(["tax-code", "get", "x1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# tax-code x1")
