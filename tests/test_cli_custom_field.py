"""Tests for `tipalti custom-field {list,get}`."""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from tipalti.cli import main


def test_custom_field_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "c1", "name": "Cost Center", "type": "string"}]}
        )
    )
    rc = main(["custom-field", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## custom-field list")
    assert "| id | name | type |" in out
    assert "Cost Center" in out


def test_custom_field_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "c1"}]})
    )
    rc = main(["custom-field", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "c1"}]


def test_custom_field_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields/c1").mock(
        return_value=httpx.Response(200, json={"id": "c1", "name": "Cost Center"})
    )
    rc = main(["custom-field", "get", "c1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# custom-field c1")
