"""HTTP-status → :class:`AfiError` mapping for Tipalti REST v2 calls.

Pure / side-effect free: every helper takes already-decoded inputs (status
code, response body string, optional ``Retry-After``) and returns an
``AfiError``. The HTTP transport layer (``api.client``) is responsible for
calling these.
"""

from __future__ import annotations

from typing import Any

import httpx

from tipalti.cli._errors import EXIT_ENV_ERROR, EXIT_USER_ERROR, AfiError


def _short_api_message(body: Any, fallback: str) -> str:
    """Pick the most useful single-line message out of an API error body."""
    if isinstance(body, dict):
        for key in ("message", "error_description", "error", "detail", "title"):
            value = body.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    if isinstance(body, str) and body.strip():
        line = body.strip().splitlines()[0]
        return line[:200]
    return fallback


def from_http_response(
    response: httpx.Response,
    *,
    resource: str | None = None,
    resource_id: str | None = None,
) -> AfiError:
    """Map an ``httpx.Response`` with non-2xx status into an :class:`AfiError`.

    ``resource`` / ``resource_id`` are used for 404 messages on ``get`` calls.
    """
    status = response.status_code
    try:
        body: Any = response.json()
    except (ValueError, httpx.DecodingError):
        body = response.text

    if status == 400:
        return AfiError(
            code=EXIT_USER_ERROR,
            message=f"bad request: {_short_api_message(body, 'invalid request')}",
            remediation="check --filter syntax / arg values",
        )
    if status == 401:
        return AfiError(
            code=EXIT_USER_ERROR,
            message="tipalti auth failed",
            remediation="check TIPALTI_CLIENT_ID/SECRET/ENV",
        )
    if status == 403:
        return AfiError(
            code=EXIT_USER_ERROR,
            message=f"forbidden: {_short_api_message(body, 'access denied')}",
            remediation="check the principal's permissions in Tipalti",
        )
    if status == 404:
        if resource and resource_id:
            msg = f"not found: {resource} {resource_id}"
        elif resource:
            msg = f"not found: {resource}"
        else:
            msg = "not found"
        return AfiError(code=EXIT_USER_ERROR, message=msg, remediation="")
    if status == 429:
        retry_after = response.headers.get("Retry-After", "").strip()
        hint = f"wait {retry_after}s and retry" if retry_after else "wait a moment and retry"
        return AfiError(
            code=EXIT_USER_ERROR,
            message="rate limited",
            remediation=hint,
        )
    if 500 <= status < 600:
        return AfiError(
            code=EXIT_USER_ERROR,
            message=f"tipalti API {status}: {_short_api_message(body, 'server error')}",
            remediation="retry later",
        )
    return AfiError(
        code=EXIT_USER_ERROR,
        message=f"tipalti API {status}: {_short_api_message(body, 'unexpected status')}",
        remediation="",
    )


def from_transport_error(exc: httpx.HTTPError) -> AfiError:
    """Map a network/transport failure into an :class:`AfiError`."""
    return AfiError(
        code=EXIT_ENV_ERROR,
        message=f"cannot reach tipalti: {exc.__class__.__name__}: {exc}",
        remediation="check connectivity / TIPALTI_ENV",
    )
