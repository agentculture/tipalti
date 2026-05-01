"""Tests for tipalti.api.client.TipaltiClient."""

from __future__ import annotations

import time

import httpx
import pytest
import respx

from tipalti.api._env import TipaltiEnv
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.api.client import TipaltiClient, _normalize_envelope
from tipalti.cli._errors import EXIT_USER_ERROR, AfiError


def _env() -> TipaltiEnv:
    return TipaltiEnv(
        client_id="id-1",
        client_secret="secret",
        env="sandbox",
        api_base="https://api.sandbox.tipalti.com",
        token_url="https://api.sandbox.tipalti.com/oauth2/token",
    )


@pytest.fixture
def primed(isolated_cache):
    """Prime the on-disk cache so tests don't have to mock token endpoints."""
    env = _env()
    write_cache(
        env,
        CachedToken(
            "fake-token",
            int(time.time()) + 3600,
            env.env,
            _client_id_hash(env.client_id),
        ),
    )
    return env


# ---- envelope normalization ------------------------------------------------


def test_normalize_envelope_items_field() -> None:
    env = _normalize_envelope({"items": [{"id": 1}], "nextPageToken": "tok"}, limit=1)
    assert env == {"items": [{"id": 1}], "next_cursor": "tok"}


def test_normalize_envelope_value_field_odata() -> None:
    env = _normalize_envelope(
        {"value": [{"id": "a"}, {"id": "b"}], "@odata.nextLink": "skip=2"},
        limit=2,
    )
    assert env["items"] == [{"id": "a"}, {"id": "b"}]
    assert env["next_cursor"] == "skip=2"


def test_normalize_envelope_short_page_drops_cursor() -> None:
    env = _normalize_envelope({"items": [{"id": 1}], "nextPageToken": "tok"}, limit=10)
    assert env["next_cursor"] is None


def test_normalize_envelope_bare_array() -> None:
    env = _normalize_envelope([{"id": 1}], limit=10)
    assert env == {"items": [{"id": 1}], "next_cursor": None}


# ---- list / get -------------------------------------------------------------


def test_payee_list_happy_path(primed, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://api.sandbox.tipalti.com/v2/payees").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "p1"}], "nextPageToken": "next-tok"}
        )
    )
    with TipaltiClient(primed) as client:
        envelope = client.payees.list(limit=1)
    assert envelope == {"items": [{"id": "p1"}], "next_cursor": "next-tok"}
    assert route.call_count == 1
    call = route.calls.last
    assert call.request.headers["authorization"] == "Bearer fake-token"
    url = str(call.request.url)
    assert "top=1" in url and ("$top=1" in url or "%24top=1" in url)


def test_invoice_list_with_filter_and_cursor(primed, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://api.sandbox.tipalti.com/v2/invoices").mock(
        return_value=httpx.Response(200, json={"items": [], "nextPageToken": ""})
    )
    with TipaltiClient(primed) as client:
        client.invoices.list(limit=10, cursor="abc", filter="status eq 'Approved'")
    url = str(route.calls.last.request.url)
    assert "%24filter=status+eq+%27Approved%27" in url or "$filter=status" in url
    assert "$skiptoken=abc" in url or "%24skiptoken=abc" in url


def test_bill_get_happy_path(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/bills/B-1").mock(
        return_value=httpx.Response(200, json={"id": "B-1", "status": "Open"})
    )
    with TipaltiClient(primed) as client:
        record = client.bills.get("B-1")
    assert record == {"id": "B-1", "status": "Open"}


def test_get_404_includes_resource(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/payees/missing").mock(
        return_value=httpx.Response(404, json={})
    )
    with TipaltiClient(primed) as client:
        with pytest.raises(AfiError) as exc:
            client.payees.get("missing")
    assert exc.value.code == EXIT_USER_ERROR
    assert exc.value.message == "not found: payee missing"


def test_list_429_retries_once(primed, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://api.sandbox.tipalti.com/v2/payees").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={}),
            httpx.Response(200, json={"items": []}),
        ]
    )
    with TipaltiClient(primed) as client:
        envelope = client.payees.list(limit=1)
    assert envelope["items"] == []
    assert route.call_count == 2


def test_list_429_after_retry_raises(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/payees").mock(
        return_value=httpx.Response(429, headers={"Retry-After": "0"}, json={})
    )
    with TipaltiClient(primed) as client:
        with pytest.raises(AfiError) as exc:
            client.payees.list(limit=1)
    assert exc.value.message == "rate limited"


def test_list_5xx_retries_then_succeeds(primed, respx_mock: respx.MockRouter) -> None:
    route = respx_mock.get("https://api.sandbox.tipalti.com/v2/payees").mock(
        side_effect=[
            httpx.Response(503, json={}),
            httpx.Response(200, json={"items": [{"id": "p1"}]}),
        ]
    )
    with TipaltiClient(primed) as client:
        envelope = client.payees.list(limit=1)
    assert envelope["items"] == [{"id": "p1"}]
    assert route.call_count == 2


# ---- whoami ----------------------------------------------------------------


def test_whoami_authenticated(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/me").mock(
        return_value=httpx.Response(200, json={"id": "me-1", "name": "Alice"})
    )
    with TipaltiClient(primed) as client:
        result = client.whoami()
    assert result["status"] == "authenticated"
    assert result["principal"]["id"] == "me-1"
    assert result["env"] == "sandbox"


def test_whoami_401_returns_unauthenticated(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/v2/me").mock(
        return_value=httpx.Response(401, json={})
    )
    with TipaltiClient(primed) as client:
        result = client.whoami()
    assert result["status"] == "unauthenticated"
    assert result["principal"] is None
