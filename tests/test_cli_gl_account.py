"""Tests for `tipalti gl-account {list,get}`."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from tipalti.cli import main


def test_gl_account_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "g1", "name": "Cash", "code": "1000"}]}
        )
    )
    rc = main(["gl-account", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## gl-account list")
    assert "| id | name | code |" in out
    assert "Cash" in out


def test_gl_account_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "g1"}]})
    )
    rc = main(["gl-account", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "g1"}]


def test_gl_account_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts/g1").mock(
        return_value=httpx.Response(200, json={"id": "g1", "name": "Cash"})
    )
    rc = main(["gl-account", "get", "g1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# gl-account g1")
