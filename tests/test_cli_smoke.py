"""Smoke tests for tipalti's CLI: --version and no-arg help."""

from __future__ import annotations

import pytest

from tipalti import __version__
from tipalti.cli import main
from tipalti.explain import known_paths


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


def test_bill_noun_removed(capsys: pytest.CaptureFixture[str]) -> None:
    # An invalid subcommand is rejected by argparse before dispatch, so the
    # parser's error() raises SystemExit(EXIT_USER_ERROR) rather than main()
    # returning a code.
    with pytest.raises(SystemExit) as exc:
        main(["bill", "list"])
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "invalid choice" in err or "bill" in err


def test_explain_drops_bill() -> None:
    # Per-noun explain coverage (CLI level) lives in
    # tests/test_cli_learn.py::test_explain_new_entries; here we only assert
    # the removed bill noun has no lingering catalog entry.
    assert ("bill",) not in known_paths()
