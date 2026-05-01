"""Tests for tipalti.api._env.load_env."""

from __future__ import annotations

import pytest

from tipalti.api._env import (
    DEFAULT_ENV,
    VALID_ENVS,
    TipaltiEnv,
    load_env,
)
from tipalti.cli._errors import EXIT_ENV_ERROR, AfiError


def test_load_env_defaults_to_sandbox() -> None:
    env = load_env({"TIPALTI_CLIENT_ID": "id", "TIPALTI_CLIENT_SECRET": "s"})
    assert isinstance(env, TipaltiEnv)
    assert env.env == DEFAULT_ENV == "sandbox"
    assert env.api_base == "https://api.sandbox.tipalti.com"
    assert env.token_url == "https://api.sandbox.tipalti.com/oauth2/token"
    assert env.client_id == "id"
    assert env.client_secret == "s"


def test_load_env_production() -> None:
    env = load_env(
        {"TIPALTI_CLIENT_ID": "id", "TIPALTI_CLIENT_SECRET": "s", "TIPALTI_ENV": "production"}
    )
    assert env.env == "production"
    assert env.api_base == "https://api.tipalti.com"
    assert env.token_url == "https://api.tipalti.com/oauth2/token"


def test_load_env_overrides_url() -> None:
    env = load_env(
        {
            "TIPALTI_CLIENT_ID": "id",
            "TIPALTI_CLIENT_SECRET": "s",
            "TIPALTI_API_BASE": "https://custom.example.com/",
            "TIPALTI_TOKEN_URL": "https://custom.example.com/oauth/token",
        }
    )
    assert env.api_base == "https://custom.example.com"  # trailing slash stripped
    assert env.token_url == "https://custom.example.com/oauth/token"


def test_load_env_missing_creds_raises() -> None:
    with pytest.raises(AfiError) as exc:
        load_env({})
    assert exc.value.code == EXIT_ENV_ERROR
    assert "TIPALTI_CLIENT_ID" in exc.value.message


def test_load_env_blank_creds_raises() -> None:
    with pytest.raises(AfiError) as exc:
        load_env({"TIPALTI_CLIENT_ID": "  ", "TIPALTI_CLIENT_SECRET": ""})
    assert exc.value.code == EXIT_ENV_ERROR


def test_load_env_unknown_env_raises() -> None:
    with pytest.raises(AfiError) as exc:
        load_env(
            {
                "TIPALTI_CLIENT_ID": "id",
                "TIPALTI_CLIENT_SECRET": "s",
                "TIPALTI_ENV": "staging",
            }
        )
    assert exc.value.code == EXIT_ENV_ERROR
    assert "staging" in exc.value.message
    for valid in VALID_ENVS:
        assert valid in exc.value.remediation


def test_load_env_case_insensitive() -> None:
    env = load_env(
        {
            "TIPALTI_CLIENT_ID": "id",
            "TIPALTI_CLIENT_SECRET": "s",
            "TIPALTI_ENV": "PRODUCTION",
        }
    )
    assert env.env == "production"
