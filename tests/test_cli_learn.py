"""Tests for `tipalti learn` and `tipalti explain`."""

from __future__ import annotations

import json

import pytest

from tipalti.cli import main


def test_learn_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    out = capsys.readouterr().out
    assert len(out) >= 200
    for marker in ["purpose", "commands", "exit", "--json", "explain"]:
        assert marker.lower() in out.lower()


def test_learn_json_parseable(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["tool"] == "tipalti"
    assert any(c["path"] == ["whoami"] for c in payload["commands"])
    for path in (
        ["payee", "list"],
        ["invoice", "list"],
        ["payment", "list"],
        ["payer-entity", "list"],
        ["gl-account", "list"],
        ["custom-field", "list"],
        ["payment-term", "list"],
        ["tax-code", "list"],
    ):
        assert any(c["path"] == path for c in payload["commands"])
    assert not any(c["path"] == ["bill", "list"] for c in payload["commands"])
    assert "TIPALTI_CLIENT_ID" in payload["env_vars"]


def test_learn_mentions_new_nouns(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["learn"]) == 0
    out = capsys.readouterr().out
    for noun in (
        "payment",
        "payer-entity",
        "gl-account",
        "custom-field",
        "payment-term",
        "tax-code",
    ):
        assert noun in out
    assert "bill" not in out


def test_explain_self(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", "tipalti"]) == 0
    assert capsys.readouterr().out.startswith("#")


@pytest.mark.parametrize(
    "path",
    [
        ["auth"],
        ["payee"],
        ["payee", "list"],
        ["payee", "get"],
        ["invoice"],
        ["invoice", "list"],
        ["invoice", "get"],
        ["payment"],
        ["payment", "list"],
        ["payment", "get"],
        ["payer-entity"],
        ["payer-entity", "list"],
        ["payer-entity", "get"],
        ["gl-account"],
        ["gl-account", "list"],
        ["gl-account", "get"],
        ["custom-field"],
        ["custom-field", "list"],
        ["custom-field", "get"],
        ["payment-term"],
        ["payment-term", "list"],
        ["payment-term", "get"],
        ["tax-code"],
        ["tax-code", "list"],
        ["tax-code", "get"],
    ],
)
def test_explain_new_entries(capsys: pytest.CaptureFixture[str], path: list[str]) -> None:
    assert main(["explain", *path]) == 0
    out = capsys.readouterr().out
    assert out.startswith("#")


def test_explain_unknown_path_fails_with_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["explain", "zzz-not-a-real-noun"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err
