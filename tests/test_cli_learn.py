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


def test_explain_self(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["explain", "tipalti"]) == 0
    assert capsys.readouterr().out.startswith("#")


def test_explain_unknown_path_fails_with_hint(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = main(["explain", "zzz-not-a-real-noun"])
    assert rc != 0
    err = capsys.readouterr().err
    assert "error:" in err
    assert "hint:" in err
