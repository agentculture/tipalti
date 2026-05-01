"""Tests for tipalti.api.errors."""

from __future__ import annotations

import httpx
import pytest

from tipalti.api.errors import from_http_response, from_transport_error
from tipalti.cli._errors import EXIT_ENV_ERROR, EXIT_USER_ERROR


def _resp(status: int, body: object = b"", headers: dict[str, str] | None = None) -> httpx.Response:
    if isinstance(body, (dict, list)):
        return httpx.Response(status, json=body, headers=headers or {})
    return httpx.Response(
        status,
        content=body if isinstance(body, bytes) else str(body).encode(),
        headers=headers or {},
    )


@pytest.mark.parametrize(
    "status,fragment",
    [
        (400, "bad request"),
        (401, "auth failed"),
        (403, "forbidden"),
        (429, "rate limited"),
        (500, "tipalti API 500"),
        (502, "tipalti API 502"),
        (503, "tipalti API 503"),
    ],
)
def test_from_http_response_status_messages(status: int, fragment: str) -> None:
    err = from_http_response(_resp(status, {"message": "x"}))
    assert err.code == EXIT_USER_ERROR
    assert fragment in err.message


def test_404_with_resource_id() -> None:
    err = from_http_response(_resp(404, {}), resource="payee", resource_id="abc")
    assert err.message == "not found: payee abc"


def test_404_without_resource_id() -> None:
    err = from_http_response(_resp(404, {}))
    assert err.message == "not found"


def test_429_includes_retry_after() -> None:
    err = from_http_response(_resp(429, {}, headers={"Retry-After": "7"}))
    assert "7s" in err.remediation


def test_short_api_message_picks_message_field() -> None:
    err = from_http_response(_resp(400, {"message": "bad filter syntax"}))
    assert "bad filter syntax" in err.message


def test_short_api_message_text_fallback() -> None:
    err = from_http_response(_resp(500, "raw plain text"))
    assert "raw plain text" in err.message


def test_from_transport_error_is_env_error() -> None:
    err = from_transport_error(httpx.ConnectError("dns lookup failed"))
    assert err.code == EXIT_ENV_ERROR
    assert "cannot reach tipalti" in err.message
    assert "ConnectError" in err.message
