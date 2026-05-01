"""CLI-agnostic HTTP layer for the Tipalti REST v2 API.

This subpackage knows nothing about argparse or the CLI's emit helpers.
Any caller (the CLI in this repo, a different harness, a notebook) can use
:class:`TipaltiClient` directly; failures surface as
:class:`tipalti.cli._errors.AfiError` with HTTP-aware codes / messages /
remediations.
"""

from __future__ import annotations

from tipalti.api._env import TipaltiEnv, load_env
from tipalti.api.client import TipaltiClient

__all__ = ["TipaltiClient", "TipaltiEnv", "load_env"]
