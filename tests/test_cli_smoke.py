"""Smoke tests for tipalti's CLI: --version and no-arg help."""

from __future__ import annotations

import pytest

from tipalti import __version__
from tipalti.cli import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_no_args_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    out = capsys.readouterr().out
    assert "tipalti" in out
    assert "learn" in out
    assert "explain" in out
    assert "whoami" in out
