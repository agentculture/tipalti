"""High-level Tipalti REST v2 client used by the CLI commands.

Boundaries:

* No argparse, no ``emit_*``: the CLI is a thin caller around this module.
* Every failure surfaces as :class:`tipalti.cli._errors.AfiError` (HTTP errors
  via :mod:`tipalti.api.errors`, transport errors as ``EXIT_ENV_ERROR``).
* Single-retry policy on 429 (honoring ``Retry-After``, capped at 10s) and
  5xx (1s linear backoff). No more — agents own higher-level retry policy.

Pagination model: ``list_*`` methods return ``{"items", "next_cursor"}``
envelopes. ``next_cursor`` is the literal ``$skiptoken`` value to feed back
in via ``--cursor``.
"""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

from tipalti.api._env import TipaltiEnv, load_env
from tipalti.api.auth import get_token
from tipalti.api.errors import from_http_response, from_transport_error

DEFAULT_TIMEOUT = 30.0
MAX_RETRY_AFTER_SECONDS = 10.0
DEFAULT_LIMIT = 100
MAX_LIMIT = 500
RETRY_STATUSES = frozenset({429, 500, 502, 503, 504})


def _coerce_retry_after(value: str | None) -> float:
    if not value:
        return 0.0
    try:
        return min(float(value), MAX_RETRY_AFTER_SECONDS)
    except ValueError:
        return 0.0


def _extract_skiptoken_from_url(link: str) -> str | None:
    """Extract ``$skiptoken`` (or ``$skip``) from an OData ``@odata.nextLink`` URL.

    The rest of the client treats ``next_cursor`` as the literal cursor
    token to feed back as ``$skiptoken`` on the next request, so storing a
    full URL here would round-trip as an invalid query parameter.
    """
    try:
        qs = parse_qs(urlparse(link).query)
    except ValueError:
        return None
    for key in ("$skiptoken", "$skip"):
        value = qs.get(key)
        if value:
            return value[0]
    return None


_ITEMS_KEYS = ("items", "value", "data")
_DIRECT_CURSOR_KEYS = ("nextPageToken", "next_cursor", "nextCursor")


def _pick_items(body: Any) -> list[Any]:
    """Pull the records list out of a list-shape response body."""
    if isinstance(body, list):
        return list(body)
    if isinstance(body, dict):
        for key in _ITEMS_KEYS:
            value = body.get(key)
            if isinstance(value, list):
                return list(value)
    return []


def _pick_cursor(body: Any) -> str | None:
    """Pull a literal cursor token out of a list-shape response body."""
    if not isinstance(body, dict):
        return None
    for key in _DIRECT_CURSOR_KEYS:
        value = body.get(key)
        if isinstance(value, str) and value:
            return value
    link = body.get("@odata.nextLink")
    if isinstance(link, str) and link:
        return _extract_skiptoken_from_url(link)
    return None


def _normalize_envelope(body: Any, limit: int) -> dict[str, Any]:
    """Map a Tipalti list response into ``{"items", "next_cursor"}``.

    Accepts both ``items``/``nextPageToken`` and OData ``value``/
    ``@odata.nextLink`` shapes. ``next_cursor`` is always a literal cursor
    token (never a URL); short pages drop the cursor defensively.
    """
    items = _pick_items(body)
    next_cursor = _pick_cursor(body)
    if next_cursor and len(items) < limit:
        next_cursor = None
    return {"items": items, "next_cursor": next_cursor}


class _ResourceGroup:
    def __init__(self, client: "TipaltiClient", path: str, name: str) -> None:
        self._client = client
        self._path = path
        self._name = name

    def list(
        self,
        *,
        limit: int = DEFAULT_LIMIT,
        cursor: str | None = None,
        filter: str | None = None,  # noqa: A002 — matches the user-facing flag
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"$top": min(max(limit, 1), MAX_LIMIT)}
        if cursor:
            params["$skiptoken"] = cursor
        if filter:
            params["$filter"] = filter
        response = self._client._request("GET", self._path, params=params)
        return _normalize_envelope(response.json(), limit=params["$top"])

    def get(self, resource_id: str) -> Any:
        response = self._client._request(
            "GET",
            f"{self._path}/{resource_id}",
            resource=self._name,
            resource_id=resource_id,
        )
        return response.json()


class TipaltiClient:
    """Thin httpx wrapper that handles auth, retry, and error mapping."""

    def __init__(
        self,
        env: TipaltiEnv,
        *,
        transport: httpx.BaseTransport | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self._env = env
        self._transport = transport
        self._http = httpx.Client(
            base_url=env.api_base,
            timeout=timeout,
            transport=transport,
            headers={"Accept": "application/json"},
        )
        self.payees = _ResourceGroup(self, "/v2/payees", "payee")
        self.invoices = _ResourceGroup(self, "/v2/invoices", "invoice")
        self.bills = _ResourceGroup(self, "/v2/bills", "bill")

    @classmethod
    def from_env(cls, **kwargs: Any) -> "TipaltiClient":
        return cls(load_env(), **kwargs)

    @property
    def env(self) -> TipaltiEnv:
        return self._env

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "TipaltiClient":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    # ---- auth -----------------------------------------------------------------

    def _auth_headers(self) -> dict[str, str]:
        token = get_token(self._env, transport=self._transport)
        return {"Authorization": f"Bearer {token.access_token}"}

    # ---- whoami ---------------------------------------------------------------

    def whoami(self) -> dict[str, Any]:
        """Probe the active principal. Returns ``{status, principal, env}``.

        Treats 401 as ``unauthenticated`` (probe semantics, not an error).
        Other HTTP errors propagate as :class:`AfiError`. The CLI layer
        also catches the ``EXIT_ENV_ERROR`` path (missing creds) and maps
        it to the same ``unauthenticated`` shape.
        """
        response = self._raw_request("GET", "/v2/me")
        if response.status_code == 401:
            return {"status": "unauthenticated", "principal": None, "env": self._env.env}
        if response.status_code >= 400:
            raise from_http_response(response)
        try:
            principal = response.json()
        except ValueError:
            principal = None
        return {
            "status": "authenticated",
            "principal": principal,
            "env": self._env.env,
        }

    # ---- internals ------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        resource: str | None = None,
        resource_id: str | None = None,
    ) -> httpx.Response:
        response = self._raw_request(method, path, params=params)
        if response.status_code >= 400:
            raise from_http_response(response, resource=resource, resource_id=resource_id)
        return response

    def _raw_request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Make a request with a single-attempt retry on 429 / 5xx / transport.

        The retry delay is computed *once* per iteration: ``Retry-After`` for
        429 (capped at ``MAX_RETRY_AFTER_SECONDS``), ``1.0s`` for 5xx and
        transport errors. We don't stack a fixed backoff on top of
        ``Retry-After`` — sleeping ``Retry-After: 7`` should wait exactly 7s.
        """
        delay = 0.0
        last_response: httpx.Response | None = None
        for attempt_index in range(2):
            if delay > 0:
                time.sleep(delay)
            try:
                response = self._http.request(
                    method,
                    path,
                    params=params,
                    headers=self._auth_headers(),
                )
            except httpx.HTTPError as exc:
                if attempt_index == 0:
                    delay = 1.0
                    continue
                raise from_transport_error(exc) from exc

            if response.status_code in RETRY_STATUSES and attempt_index == 0:
                if response.status_code == 429:
                    delay = _coerce_retry_after(response.headers.get("Retry-After"))
                else:
                    delay = 1.0
                last_response = response
                continue
            return response

        # Both attempts produced retryable failures; surface the last one.
        assert last_response is not None  # nosec B101
        return last_response
