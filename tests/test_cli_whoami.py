"""Tests for `tipalti whoami` (auth probe stub)."""

from __future__ import annotations

import json

import pytest

from tipalti.cli import main


def test_whoami_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["whoami"]) == 0
    assert "unauthenticated" in capsys.readouterr().out


def test_whoami_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["whoami", "--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "unauthenticated"
    assert payload["principal"] is None
