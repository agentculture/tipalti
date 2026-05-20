# v0.2.0 Read-Only REST v2 Nouns — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct the Tipalti REST resource path prefix to `/api/v1/`, remove the non-existent `bill` noun, and add six read-only `list`/`get` nouns (payment, payer-entity, gl-account, custom-field, payment-term, tax-code).

**Architecture:** Pure reuse of the existing `_ResourceGroup` (api) + `register_noun_group` (cli) helpers — each new noun is a one-line client registration plus a ~15-line command module. The path correction is a mechanical string change with a regression-guard test. `whoami` is repointed from the non-existent `/v2/me` to a `/api/v1/payer-entities` reachability probe.

**Tech Stack:** Python 3, `httpx`, `argparse`, `pytest` + `respx` (HTTP mocking), `uv` for env/test running.

**Conventions:**

- Run tests with `uv run pytest <path> -v`.
- CLI noun names are kebab-case (`payer-entity`); client attributes are underscored plurals (`payer_entities`).
- Commit after each task. Branch is `feat/read-only-nouns-v0.2.0` (already created).
- TDD: write the failing test, watch it fail, implement, watch it pass, commit.

---

## Task 1: Correct resource path prefix `/v2/` → `/api/v1/` and drop the `bills` group

**Files:**

- Modify: `tipalti/api/client.py:155-157` (resource-group registrations)
- Modify: `tipalti/api/client.py:192` (`whoami` probe path — handled in Task 2; here only the three resource groups + bill removal)
- Test: `tests/test_api_client.py`

- [ ] **Step 1: Write the failing path-prefix regression test**

Add to `tests/test_api_client.py` (after the `primed` fixture):

```python
def test_all_resource_paths_use_api_v1_prefix(primed) -> None:
    """Every registered resource group must live under /api/v1/."""
    with TipaltiClient(primed) as client:
        groups = [
            client.payees,
            client.invoices,
            client.payments,
            client.payer_entities,
            client.gl_accounts,
            client.custom_fields,
            client.payment_terms,
            client.tax_codes,
        ]
    for group in groups:
        assert group._path.startswith("/api/v1/"), group._path
    # The bill noun is removed entirely.
    assert not hasattr(client, "bills")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `uv run pytest tests/test_api_client.py::test_all_resource_paths_use_api_v1_prefix -v`
Expected: FAIL — `AttributeError: 'TipaltiClient' object has no attribute 'payments'` (the new groups don't exist yet) / paths still `/v2/`.

- [ ] **Step 3: Re-base the existing groups and add the six new ones**

In `tipalti/api/client.py`, replace the three registrations at lines 155-157:

```python
        self.payees = _ResourceGroup(self, "/v2/payees", "payee")
        self.invoices = _ResourceGroup(self, "/v2/invoices", "invoice")
        self.bills = _ResourceGroup(self, "/v2/bills", "bill")
```

with:

```python
        self.payees = _ResourceGroup(self, "/api/v1/payees", "payee")
        self.invoices = _ResourceGroup(self, "/api/v1/invoices", "invoice")
        self.payments = _ResourceGroup(self, "/api/v1/payments", "payment")
        self.payer_entities = _ResourceGroup(self, "/api/v1/payer-entities", "payer-entity")
        self.gl_accounts = _ResourceGroup(self, "/api/v1/gl-accounts", "gl-account")
        self.custom_fields = _ResourceGroup(self, "/api/v1/custom-fields", "custom-field")
        self.payment_terms = _ResourceGroup(self, "/api/v1/payment-terms", "payment-term")
        self.tax_codes = _ResourceGroup(self, "/api/v1/tax-codes", "tax-code")
```

- [ ] **Step 4: Fix the existing API tests that reference `/v2/` paths and the removed `bills` group**

In `tests/test_api_client.py`:

Replace every `https://api.sandbox.tipalti.com/v2/payees` with `.../api/v1/payees` and every `.../v2/invoices` with `.../api/v1/invoices` (in `test_payee_list_happy_path`, `test_invoice_list_with_filter_and_cursor`, `test_get_404_includes_resource`, `test_list_429_retries_once`, `test_list_429_after_retry_raises`, `test_list_5xx_retries_then_succeeds`, `test_429_retry_after_does_not_oversleep`).

Replace the `test_bill_get_happy_path` test (lines ~122-128) with a payment equivalent:

```python
def test_payment_get_happy_path(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments/PMT-1").mock(
        return_value=httpx.Response(200, json={"id": "PMT-1", "status": "Paid"})
    )
    with TipaltiClient(primed) as client:
        record = client.payments.get("PMT-1")
    assert record == {"id": "PMT-1", "status": "Paid"}
```

Also update the two OData `@odata.nextLink` literals in `test_normalize_envelope_*` from `/v2/payees` to `/api/v1/payees` (cosmetic, but keeps the file consistent).

- [ ] **Step 5: Run the API client tests**

Run: `uv run pytest tests/test_api_client.py -v`
Expected: PASS for all. The `whoami` tests still pass here — Task 1 changes neither the `whoami` method nor its tests, which both still use `/v2/me`. They are repointed in Task 2.

- [ ] **Step 6: Commit**

```bash
git add tipalti/api/client.py tests/test_api_client.py
git commit -m "fix: re-base resource paths to /api/v1/ and drop bills group"
```

---

## Task 2: Repoint `whoami` to a `/api/v1/payer-entities` reachability probe

**Files:**

- Modify: `tipalti/api/client.py:184-205` (`whoami` method)
- Modify: `tipalti/cli/_commands/whoami.py:49-58` (drop principal digging)
- Test: `tests/test_api_client.py`, `tests/test_cli_whoami.py`

REST v2 has no identity endpoint, so `whoami` confirms reachability + auth only. `principal` is always `None` when reachable.

- [ ] **Step 1: Update the API-level whoami tests to the new probe path/shape**

In `tests/test_api_client.py`, replace `test_whoami_authenticated` and `test_whoami_401_returns_unauthenticated`:

```python
def test_whoami_authenticated(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "e1"}]})
    )
    with TipaltiClient(primed) as client:
        result = client.whoami()
    assert result["status"] == "authenticated"
    assert result["principal"] is None
    assert result["env"] == "sandbox"


def test_whoami_401_returns_unauthenticated(primed, respx_mock: respx.MockRouter) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(401, json={})
    )
    with TipaltiClient(primed) as client:
        result = client.whoami()
    assert result["status"] == "unauthenticated"
    assert result["principal"] is None
```

- [ ] **Step 2: Run to verify they fail**

Run: `uv run pytest tests/test_api_client.py -v -k whoami`
Expected: FAIL — whoami still GETs `/v2/me`, so the `/api/v1/payer-entities` mock is never hit (respx raises on the unmocked `/v2/me` request, or returns the wrong shape).

- [ ] **Step 3: Rewrite the `whoami` method**

In `tipalti/api/client.py`, replace the `whoami` method body (lines ~184-205):

```python
    def whoami(self) -> dict[str, Any]:
        """Probe auth reachability. Returns ``{status, principal, env}``.

        REST v2 exposes no identity endpoint, so this is a reachability +
        auth probe against the cheapest documented collection
        (``/api/v1/payer-entities`` with ``$top=1``). ``principal`` is always
        ``None`` — there is no principal payload to return. ``401`` reports
        ``unauthenticated`` (probe semantics); other HTTP errors propagate.
        """
        response = self._raw_request(
            "GET", "/api/v1/payer-entities", params={"$top": 1}
        )
        if response.status_code == 401:
            return {"status": "unauthenticated", "principal": None, "env": self._env.env}
        if response.status_code >= 400:
            raise from_http_response(response)
        return {"status": "authenticated", "principal": None, "env": self._env.env}
```

- [ ] **Step 4: Simplify the CLI whoami renderer**

In `tipalti/cli/_commands/whoami.py`, replace the principal-digging block (lines ~49-58):

```python
    principal = result.get("principal")
    fields: dict[str, object] = {"status": "authenticated", "env": result.get("env")}
    if isinstance(principal, dict):
        for key in ("id", "name", "email", "subject", "sub", "client_id"):
            value = principal.get(key)
            if value is not None and key not in fields:
                fields[key] = value
    elif principal is not None:
        fields["principal"] = principal
    emit_result(render_kv_md("tipalti whoami", fields), json_mode=False)
    return 0
```

with:

```python
    fields: dict[str, object] = {"status": "authenticated", "env": result.get("env")}
    emit_result(render_kv_md("tipalti whoami", fields), json_mode=False)
    return 0
```

- [ ] **Step 5: Update the CLI whoami tests**

In `tests/test_cli_whoami.py`, replace the `/v2/me` mocks in `test_whoami_401_is_unauthenticated_exit_zero` and `test_whoami_authenticated_markdown`:

In `test_whoami_401_is_unauthenticated_exit_zero`, change the mock URL from `https://api.sandbox.tipalti.com/v2/me` to `https://api.sandbox.tipalti.com/api/v1/payer-entities`.

Replace `test_whoami_authenticated_markdown` body's mock + assertions:

```python
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "e1"}]})
    )
    rc = main(["whoami"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "authenticated" in out
    assert "**env:** sandbox" in out
```

- [ ] **Step 6: Run the whoami tests**

Run: `uv run pytest tests/test_api_client.py tests/test_cli_whoami.py -v -k whoami`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add tipalti/api/client.py tipalti/cli/_commands/whoami.py tests/test_api_client.py tests/test_cli_whoami.py
git commit -m "fix: repoint whoami to /api/v1/payer-entities reachability probe"
```

---

## Task 3: Remove the `bill` noun (command + registration + tests)

**Files:**

- Delete: `tipalti/cli/_commands/bill.py`
- Delete: `tests/test_cli_bill.py`
- Modify: `tipalti/cli/__init__.py:19,55` (drop import + registration)
- Test: `tests/test_cli_smoke.py`

- [ ] **Step 1: Write a failing test that `tipalti bill` is rejected**

Add to `tests/test_cli_smoke.py`:

```python
def test_bill_noun_removed(capsys) -> None:
    from tipalti.cli import main

    rc = main(["bill", "list"])
    assert rc == 1
    err = capsys.readouterr().err
    assert "invalid choice" in err or "bill" in err
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_smoke.py::test_bill_noun_removed -v`
Expected: FAIL — `bill` is still registered, so it doesn't return exit 1 with "invalid choice" (it tries to run and fails differently, e.g. exit 2 missing creds).

- [ ] **Step 3: Drop the `bill` import and registration**

In `tipalti/cli/__init__.py`, remove the import line (line 19):

```python
from tipalti.cli._commands import bill as _bill_cmd
```

and the registration line (line 55):

```python
    _bill_cmd.register(sub)
```

- [ ] **Step 4: Delete the bill command module and its tests**

```bash
git rm tipalti/cli/_commands/bill.py tests/test_cli_bill.py
```

- [ ] **Step 5: Run the smoke test**

Run: `uv run pytest tests/test_cli_smoke.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "feat: remove bill noun (not a real REST v2 resource)"
```

---

## Task 4: Add the `payment` noun (`list`/`get`)

This task establishes the pattern; Tasks 5-9 repeat it for the other five nouns.

**Files:**

- Create: `tipalti/cli/_commands/payment.py`
- Modify: `tipalti/cli/__init__.py` (import + register)
- Test: `tests/test_cli_payment.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_payment.py`:

```python
"""Tests for `tipalti payment {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_payment_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {"id": "PMT-1", "refCode": "R1", "status": "Paid",
                     "amount": "100", "currency": "USD"},
                ],
                "nextPageToken": "",
            },
        )
    )
    rc = main(["payment", "list", "--limit", "1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payment list")
    assert "| id | refCode | status | amount | currency |" in out
    assert "PMT-1" in out


def test_payment_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "PMT-1"}], "nextPageToken": "t"})
    )
    rc = main(["payment", "list", "--limit", "1", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [{"id": "PMT-1"}]
    assert payload["next_cursor"] == "t"


def test_payment_get_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments/PMT-1").mock(
        return_value=httpx.Response(200, json={"id": "PMT-1", "status": "Paid"})
    )
    rc = main(["payment", "get", "PMT-1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# payment PMT-1")
    assert "**id:** PMT-1" in out


def test_payment_get_404(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payments/missing").mock(
        return_value=httpx.Response(404, json={})
    )
    rc = main(["payment", "get", "missing"])
    assert rc == 1
    assert "not found: payment missing" in capsys.readouterr().err
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_payment.py -v`
Expected: FAIL — exit 1 "invalid choice: 'payment'" (noun not registered).

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/payment.py`:

```python
"""``tipalti payment {list,get}`` — read-only Payments verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payment",
        group_help="Tipalti payments (read-only).",
        list_help="List payments.",
        list_columns=("id", "refCode", "status", "amount", "currency"),
        get_help="Get a single payment by id.",
        get_id_help="Payment id (or refCode, depending on tenant).",
        list_fetch=lambda client, args: client.payments.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payments.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add the import (alphabetically, near the other `_commands` imports):

```python
from tipalti.cli._commands import payment as _payment_cmd
```

and register it in `_build_parser` after `_payee_cmd.register(sub)`:

```python
    _payment_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_payment.py -v`
Expected: PASS (all 4).

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/payment.py tipalti/cli/__init__.py tests/test_cli_payment.py
git commit -m "feat: add payment list/get (read-only)"
```

---

## Task 5: Add the `payer-entity` noun

**Files:**

- Create: `tipalti/cli/_commands/payer_entity.py`
- Modify: `tipalti/cli/__init__.py`
- Test: `tests/test_cli_payer_entity.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_payer_entity.py` (same structure as Task 4; `auth` fixture identical — copy it verbatim):

```python
"""Tests for `tipalti payer-entity {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_payer_entity_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "e1", "name": "Entity One", "status": "Active"}]}
        )
    )
    rc = main(["payer-entity", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payer-entity list")
    assert "| id | name | status |" in out
    assert "Entity One" in out


def test_payer_entity_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "e1"}], "nextPageToken": "t"})
    )
    rc = main(["payer-entity", "list", "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["items"] == [{"id": "e1"}]


def test_payer_entity_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payer-entities/e1").mock(
        return_value=httpx.Response(200, json={"id": "e1", "name": "Entity One"})
    )
    rc = main(["payer-entity", "get", "e1"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("# payer-entity e1")
    assert "**name:** Entity One" in out
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_payer_entity.py -v`
Expected: FAIL — "invalid choice: 'payer-entity'".

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/payer_entity.py`:

```python
"""``tipalti payer-entity {list,get}`` — read-only Payer Entities verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payer-entity",
        group_help="Tipalti payer entities (read-only).",
        list_help="List payer entities.",
        list_columns=("id", "name", "status"),
        get_help="Get a single payer entity by id.",
        get_id_help="Payer entity id.",
        list_fetch=lambda client, args: client.payer_entities.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payer_entities.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add:

```python
from tipalti.cli._commands import payer_entity as _payer_entity_cmd
```

and in `_build_parser` after `_payment_cmd.register(sub)`:

```python
    _payer_entity_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_payer_entity.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/payer_entity.py tipalti/cli/__init__.py tests/test_cli_payer_entity.py
git commit -m "feat: add payer-entity list/get (read-only)"
```

---

## Task 6: Add the `gl-account` noun

**Files:**

- Create: `tipalti/cli/_commands/gl_account.py`
- Modify: `tipalti/cli/__init__.py`
- Test: `tests/test_cli_gl_account.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_gl_account.py` (copy the `auth` fixture + imports from Task 5 verbatim):

```python
"""Tests for `tipalti gl-account {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_gl_account_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "g1", "name": "Cash", "code": "1000"}]}
        )
    )
    rc = main(["gl-account", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## gl-account list")
    assert "| id | name | code |" in out
    assert "Cash" in out


def test_gl_account_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "g1"}]})
    )
    rc = main(["gl-account", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "g1"}]


def test_gl_account_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/gl-accounts/g1").mock(
        return_value=httpx.Response(200, json={"id": "g1", "name": "Cash"})
    )
    rc = main(["gl-account", "get", "g1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# gl-account g1")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_gl_account.py -v`
Expected: FAIL — "invalid choice: 'gl-account'".

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/gl_account.py`:

```python
"""``tipalti gl-account {list,get}`` — read-only GL Accounts verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="gl-account",
        group_help="Tipalti GL accounts (read-only).",
        list_help="List GL accounts.",
        list_columns=("id", "name", "code"),
        get_help="Get a single GL account by id.",
        get_id_help="GL account id.",
        list_fetch=lambda client, args: client.gl_accounts.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.gl_accounts.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add:

```python
from tipalti.cli._commands import gl_account as _gl_account_cmd
```

and in `_build_parser` after `_payer_entity_cmd.register(sub)`:

```python
    _gl_account_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_gl_account.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/gl_account.py tipalti/cli/__init__.py tests/test_cli_gl_account.py
git commit -m "feat: add gl-account list/get (read-only)"
```

---

## Task 7: Add the `custom-field` noun

**Files:**

- Create: `tipalti/cli/_commands/custom_field.py`
- Modify: `tipalti/cli/__init__.py`
- Test: `tests/test_cli_custom_field.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_custom_field.py` (copy the `auth` fixture + imports from Task 5 verbatim):

```python
"""Tests for `tipalti custom-field {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_custom_field_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "c1", "name": "Cost Center", "type": "string"}]}
        )
    )
    rc = main(["custom-field", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## custom-field list")
    assert "| id | name | type |" in out
    assert "Cost Center" in out


def test_custom_field_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "c1"}]})
    )
    rc = main(["custom-field", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "c1"}]


def test_custom_field_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/custom-fields/c1").mock(
        return_value=httpx.Response(200, json={"id": "c1", "name": "Cost Center"})
    )
    rc = main(["custom-field", "get", "c1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# custom-field c1")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_custom_field.py -v`
Expected: FAIL — "invalid choice: 'custom-field'".

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/custom_field.py`:

```python
"""``tipalti custom-field {list,get}`` — read-only Custom Fields verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="custom-field",
        group_help="Tipalti custom fields (read-only).",
        list_help="List custom fields.",
        list_columns=("id", "name", "type"),
        get_help="Get a single custom field by id.",
        get_id_help="Custom field id.",
        list_fetch=lambda client, args: client.custom_fields.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.custom_fields.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add:

```python
from tipalti.cli._commands import custom_field as _custom_field_cmd
```

and in `_build_parser` after `_gl_account_cmd.register(sub)`:

```python
    _custom_field_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_custom_field.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/custom_field.py tipalti/cli/__init__.py tests/test_cli_custom_field.py
git commit -m "feat: add custom-field list/get (read-only)"
```

---

## Task 8: Add the `payment-term` noun

**Files:**

- Create: `tipalti/cli/_commands/payment_term.py`
- Modify: `tipalti/cli/__init__.py`
- Test: `tests/test_cli_payment_term.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_payment_term.py` (copy the `auth` fixture + imports from Task 5 verbatim):

```python
"""Tests for `tipalti payment-term {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_payment_term_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "t1", "name": "Net 30", "days": 30}]}
        )
    )
    rc = main(["payment-term", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## payment-term list")
    assert "| id | name | days |" in out
    assert "Net 30" in out


def test_payment_term_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "t1"}]})
    )
    rc = main(["payment-term", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "t1"}]


def test_payment_term_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/payment-terms/t1").mock(
        return_value=httpx.Response(200, json={"id": "t1", "name": "Net 30"})
    )
    rc = main(["payment-term", "get", "t1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# payment-term t1")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_payment_term.py -v`
Expected: FAIL — "invalid choice: 'payment-term'".

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/payment_term.py`:

```python
"""``tipalti payment-term {list,get}`` — read-only Payment Terms verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="payment-term",
        group_help="Tipalti payment terms (read-only).",
        list_help="List payment terms.",
        list_columns=("id", "name", "days"),
        get_help="Get a single payment term by id.",
        get_id_help="Payment term id.",
        list_fetch=lambda client, args: client.payment_terms.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.payment_terms.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add:

```python
from tipalti.cli._commands import payment_term as _payment_term_cmd
```

and in `_build_parser` after `_custom_field_cmd.register(sub)`:

```python
    _payment_term_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_payment_term.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/payment_term.py tipalti/cli/__init__.py tests/test_cli_payment_term.py
git commit -m "feat: add payment-term list/get (read-only)"
```

---

## Task 9: Add the `tax-code` noun

**Files:**

- Create: `tipalti/cli/_commands/tax_code.py`
- Modify: `tipalti/cli/__init__.py`
- Test: `tests/test_cli_tax_code.py`

- [ ] **Step 1: Write the failing CLI tests**

Create `tests/test_cli_tax_code.py` (copy the `auth` fixture + imports from Task 5 verbatim):

```python
"""Tests for `tipalti tax-code {list,get}`."""

from __future__ import annotations

import json
import time

import httpx
import pytest
import respx

from tipalti.api._env import load_env
from tipalti.api.auth import CachedToken, _client_id_hash, write_cache
from tipalti.cli import main


@pytest.fixture
def auth(monkeypatch: pytest.MonkeyPatch, isolated_cache) -> None:
    monkeypatch.setenv("TIPALTI_CLIENT_ID", "id-1")
    monkeypatch.setenv("TIPALTI_CLIENT_SECRET", "secret")
    env = load_env()
    write_cache(
        env,
        CachedToken("fake", int(time.time()) + 3600, env.env, _client_id_hash(env.client_id)),
    )


def test_tax_code_list_markdown(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes").mock(
        return_value=httpx.Response(
            200, json={"items": [{"id": "x1", "name": "VAT", "rate": "0.20"}]}
        )
    )
    rc = main(["tax-code", "list"])
    assert rc == 0
    out = capsys.readouterr().out
    assert out.startswith("## tax-code list")
    assert "| id | name | rate |" in out
    assert "VAT" in out


def test_tax_code_list_json(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes").mock(
        return_value=httpx.Response(200, json={"items": [{"id": "x1"}]})
    )
    rc = main(["tax-code", "list", "--json"])
    assert rc == 0
    assert json.loads(capsys.readouterr().out)["items"] == [{"id": "x1"}]


def test_tax_code_get(
    auth: None, capsys: pytest.CaptureFixture[str], respx_mock: respx.MockRouter
) -> None:
    respx_mock.get("https://api.sandbox.tipalti.com/api/v1/tax-codes/x1").mock(
        return_value=httpx.Response(200, json={"id": "x1", "name": "VAT"})
    )
    rc = main(["tax-code", "get", "x1"])
    assert rc == 0
    assert capsys.readouterr().out.startswith("# tax-code x1")
```

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_tax_code.py -v`
Expected: FAIL — "invalid choice: 'tax-code'".

- [ ] **Step 3: Create the command module**

Create `tipalti/cli/_commands/tax_code.py`:

```python
"""``tipalti tax-code {list,get}`` — read-only Tax Codes verbs (REST v2)."""

from __future__ import annotations

import argparse

from tipalti.cli._listing import register_noun_group


def register(sub: argparse._SubParsersAction) -> None:
    register_noun_group(
        sub,
        noun="tax-code",
        group_help="Tipalti tax codes (read-only).",
        list_help="List tax codes.",
        list_columns=("id", "name", "rate"),
        get_help="Get a single tax code by id.",
        get_id_help="Tax code id.",
        list_fetch=lambda client, args: client.tax_codes.list(
            limit=args.limit, cursor=args.cursor, filter=args.filter
        ),
        get_fetch=lambda client, rid: client.tax_codes.get(rid),
    )
```

- [ ] **Step 4: Register the module**

In `tipalti/cli/__init__.py`, add:

```python
from tipalti.cli._commands import tax_code as _tax_code_cmd
```

and in `_build_parser` after `_payment_term_cmd.register(sub)`:

```python
    _tax_code_cmd.register(sub)
```

- [ ] **Step 5: Run the tests**

Run: `uv run pytest tests/test_cli_tax_code.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/tax_code.py tipalti/cli/__init__.py tests/test_cli_tax_code.py
git commit -m "feat: add tax-code list/get (read-only)"
```

---

## Task 10: Update the `explain` catalog (add new nouns, drop bill, fix root + whoami)

**Files:**

- Modify: `tipalti/explain/catalog.py`
- Test: `tests/test_cli_smoke.py` (or wherever explain is exercised)

- [ ] **Step 1: Write the failing explain test**

Add to `tests/test_cli_smoke.py`:

```python
import pytest

from tipalti.explain import known_paths, resolve


@pytest.mark.parametrize(
    "path",
    [
        ("payment",), ("payment", "list"), ("payment", "get"),
        ("payer-entity",), ("payer-entity", "list"), ("payer-entity", "get"),
        ("gl-account",), ("gl-account", "list"), ("gl-account", "get"),
        ("custom-field",), ("custom-field", "list"), ("custom-field", "get"),
        ("payment-term",), ("payment-term", "list"), ("payment-term", "get"),
        ("tax-code",), ("tax-code", "list"), ("tax-code", "get"),
    ],
)
def test_explain_has_new_noun_entries(path) -> None:
    assert path in known_paths()
    assert resolve(path)  # non-empty markdown


def test_explain_drops_bill() -> None:
    assert ("bill",) not in known_paths()
```

> Confirm `known_paths` / `resolve` are exported from `tipalti.explain.__init__`; the CLAUDE.md tree documents `resolve()` + `known_paths()` there. If the import names differ, adjust the import to match `tipalti/explain/__init__.py`.

- [ ] **Step 2: Run to verify it fails**

Run: `uv run pytest tests/test_cli_smoke.py -v -k explain`
Expected: FAIL — new paths not in `known_paths()`; `("bill",)` still present.

- [ ] **Step 3: Add the new catalog entries**

In `tipalti/explain/catalog.py`, add entries for each new noun + its verbs, following the existing `_PAYEE` / `_PAYEE_LIST` / `_PAYEE_GET` style. Example for `payment` (replicate the shape for the other five — payer-entity, gl-account, custom-field, payment-term, tax-code — adjusting noun text and the `tipalti <noun> ...` usage lines):

```python
_PAYMENT = """\
# tipalti payment

Read-only verbs over Tipalti's Payments resource (REST v2).

## Verbs

- `tipalti payment list` — list payments with optional `--filter`, `--limit`,
  `--cursor`.
- `tipalti payment get <id>` — fetch one payment by id.

## Usage

    tipalti payment list --limit 50
    tipalti payment list --filter "status eq 'Paid'"
    tipalti payment get <id>
"""

_PAYMENT_LIST = """\
# tipalti payment list

Lists payments from Tipalti REST v2. Same flag set as `tipalti payee list`:
`--limit`, `--cursor`, `--filter`, `--json`. One HTTP request per call.
"""

_PAYMENT_GET = """\
# tipalti payment get <id>

Fetches a single payment by id. `--json` emits the raw API record.
"""
```

Add analogous `_PAYER_ENTITY*`, `_GL_ACCOUNT*`, `_CUSTOM_FIELD*`, `_PAYMENT_TERM*`, `_TAX_CODE*` constants.

- [ ] **Step 4: Remove the bill entries**

In `tipalti/explain/catalog.py`, delete the `_BILL`, `_BILL_LIST`, `_BILL_GET` string constants and their three `ENTRIES` keys (`("bill",)`, `("bill", "list")`, `("bill", "get")`).

- [ ] **Step 5: Register the new entries in `ENTRIES`**

Add to the `ENTRIES` dict (and remove the three `bill` keys):

```python
    ("payment",): _PAYMENT,
    ("payment", "list"): _PAYMENT_LIST,
    ("payment", "get"): _PAYMENT_GET,
    ("payer-entity",): _PAYER_ENTITY,
    ("payer-entity", "list"): _PAYER_ENTITY_LIST,
    ("payer-entity", "get"): _PAYER_ENTITY_GET,
    ("gl-account",): _GL_ACCOUNT,
    ("gl-account", "list"): _GL_ACCOUNT_LIST,
    ("gl-account", "get"): _GL_ACCOUNT_GET,
    ("custom-field",): _CUSTOM_FIELD,
    ("custom-field", "list"): _CUSTOM_FIELD_LIST,
    ("custom-field", "get"): _CUSTOM_FIELD_GET,
    ("payment-term",): _PAYMENT_TERM,
    ("payment-term", "list"): _PAYMENT_TERM_LIST,
    ("payment-term", "get"): _PAYMENT_TERM_GET,
    ("tax-code",): _TAX_CODE,
    ("tax-code", "list"): _TAX_CODE_LIST,
    ("tax-code", "get"): _TAX_CODE_GET,
```

- [ ] **Step 6: Update `_ROOT` and `_WHOAMI`**

In `_ROOT`, replace the `bill` lines in the "Verbs" and "See also" sections with the six new nouns. Change the verb list to read:

```text
- `tipalti payee list` / `tipalti payee get <id>` — payees (read-only).
- `tipalti invoice list` / `tipalti invoice get <id>` — invoices.
- `tipalti payment list` / `tipalti payment get <id>` — payments.
- `tipalti payer-entity list` / `... get <id>` — payer entities.
- `tipalti gl-account list` / `... get <id>` — GL accounts.
- `tipalti custom-field list` / `... get <id>` — custom fields.
- `tipalti payment-term list` / `... get <id>` — payment terms.
- `tipalti tax-code list` / `... get <id>` — tax codes.
```

and the "See also" list: drop `tipalti explain bill`, add the six new `tipalti explain <noun>` lines.

In `_WHOAMI`, replace the body so it states `whoami` is a reachability + auth probe that returns no principal (REST v2 has no identity endpoint):

```python
_WHOAMI = """\
# tipalti whoami

Probes Tipalti auth reachability using the credentials documented in
`tipalti explain auth`. REST v2 exposes no identity endpoint, so `whoami`
confirms that credentials authenticate and the API is reachable — it does
not return a principal identity.

When no credentials are configured, when `TIPALTI_CLIENT_ID/SECRET` are
empty, or when the probe returns 401, `whoami` reports `unauthenticated`
and exits `0` (probe, not gate). Other API/transport errors propagate with
`EXIT_USER_ERROR` / `EXIT_ENV_ERROR`.

## Usage

    tipalti whoami
    tipalti whoami --json
"""
```

- [ ] **Step 7: Run the explain tests**

Run: `uv run pytest tests/test_cli_smoke.py -v`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
git add tipalti/explain/catalog.py tests/test_cli_smoke.py
git commit -m "docs: explain catalog for new nouns; drop bill; update root + whoami"
```

---

## Task 11: Refresh `learn` copy

**Files:**

- Modify: `tipalti/cli/_commands/learn.py`
- Test: `tests/test_cli_learn.py`

- [ ] **Step 1: Read the current learn copy and its test**

Run: `uv run pytest tests/test_cli_learn.py -v` and open `tipalti/cli/_commands/learn.py` to see the current noun list it prints.

- [ ] **Step 2: Write/adjust a failing assertion**

In `tests/test_cli_learn.py`, add (or extend an existing output assertion) so it requires the new nouns and forbids `bill`:

```python
def test_learn_mentions_new_nouns(capsys) -> None:
    from tipalti.cli import main

    rc = main(["learn"])
    assert rc == 0
    out = capsys.readouterr().out
    for noun in ("payment", "payer-entity", "gl-account",
                 "custom-field", "payment-term", "tax-code"):
        assert noun in out
    assert "bill" not in out
```

- [ ] **Step 3: Run to verify it fails**

Run: `uv run pytest tests/test_cli_learn.py::test_learn_mentions_new_nouns -v`
Expected: FAIL — new nouns absent / `bill` present in the learn text.

- [ ] **Step 4: Update the learn copy**

In `tipalti/cli/_commands/learn.py`, update the command-map / noun list text: remove `bill`, add the six new nouns (mirror however the existing copy enumerates payee/invoice). Keep it terse.

- [ ] **Step 5: Run the learn tests**

Run: `uv run pytest tests/test_cli_learn.py -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add tipalti/cli/_commands/learn.py tests/test_cli_learn.py
git commit -m "docs: refresh learn copy for new nouns; drop bill"
```

---

## Task 12: Full suite + lint, version bump, CLAUDE.md, CHANGELOG

**Files:**

- Modify: `CLAUDE.md`
- Modify (via script): `pyproject.toml`, `CHANGELOG.md`

- [ ] **Step 1: Run the full test suite**

Run: `uv run pytest -n auto -v`
Expected: PASS, no skips beyond the opt-in `@pytest.mark.integration` test.

- [ ] **Step 2: Run lint**

Run: `uv run flake8 tipalti tests && uv run black --check . && uv run isort --check .`
Expected: clean. If `black`/`isort` complain, run `uv run black tipalti tests && uv run isort tipalti tests` and re-check.

- [ ] **Step 3: Update CLAUDE.md**

Edit `CLAUDE.md`:

- **Status** section: bump to `v0.2.0`; note "adds payment, payer-entity, gl-account, custom-field, payment-term, tax-code read verbs; corrects REST paths to `/api/v1/`; removes the `bill` noun."
- **What this project is**: update the noun list (payees, invoices, payments, payer-entities, GL accounts, custom fields, payment terms, tax codes); drop "Bills".
- **Project shape** tree under `_commands/`: remove `bill.py`, add the six new modules.

- [ ] **Step 4: Bump the version**

Run: `python3 .claude/skills/version-bump/scripts/bump.py minor`
Expected: `pyproject.toml` version → `0.2.0`; a new `CHANGELOG.md` entry stub is prepended.

- [ ] **Step 5: Fill in the CHANGELOG entry**

Edit the new `## [0.2.0]` section in `CHANGELOG.md`:

```markdown
### Added

- tipalti payment list / payment get — read-only Payments verbs (REST v2)
- tipalti payer-entity list / payer-entity get — read-only Payer Entities verbs
- tipalti gl-account, custom-field, payment-term, tax-code — read-only list/get verbs
- explain entries for all six new nouns

### Changed

- Resource paths corrected from `/v2/...` to the documented `/api/v1/...`
- tipalti whoami now probes `/api/v1/payer-entities` (REST v2 has no identity
  endpoint); reports reachability + auth only, no principal payload

### Removed

- tipalti bill list / bill get — bills are not a standalone REST v2 resource
  (unified under invoices); the `/v2/bills` path never existed
```

- [ ] **Step 6: Verify the version**

Run: `uv run tipalti --version`
Expected: `tipalti 0.2.0`.

- [ ] **Step 7: Self-check**

Run: `steward doctor . --scope self`
Expected: PASS (portability + skills contract). If `steward` is unavailable locally, note it and rely on CI.

- [ ] **Step 8: Commit**

```bash
git add CLAUDE.md pyproject.toml CHANGELOG.md
git commit -m "chore: bump to 0.2.0; update CLAUDE.md and CHANGELOG"
```

---

## Task 13: Markdown lint the new docs

**Files:**

- The spec + plan + CHANGELOG + CLAUDE.md

- [ ] **Step 1: Lint**

Run: `markdownlint-cli2 "**/*.md"`
Expected: clean. Auto-fix with `markdownlint-cli2 --fix "**/*.md"` if needed, then re-run.

- [ ] **Step 2: Commit any fixes**

```bash
git add -A
git commit -m "style: markdownlint fixes"
```

---

## Done criteria

- `uv run pytest -n auto -v` green; only the opt-in integration test skipped.
- `uv run tipalti --version` → `0.2.0`.
- `tipalti payment|payer-entity|gl-account|custom-field|payment-term|tax-code {list,get}` all work against mocked `/api/v1/...` endpoints.
- `tipalti bill ...` rejected; no `/v2/` paths remain in `tipalti/`.
- `steward doctor . --scope self`, flake8, black, isort, markdownlint all clean.
- Ready to open a PR (version-check CI will pass — version differs from main).

## Deferred (explicitly out of scope — see spec)

- Payment batches (`/api/v1/payment-batches/{id}` + `/instructions`) — naming and nested shape unresolved.
- OAuth scope handling in `auth.py` — revisit only if live-sandbox reads 403.
- Mutations, iFrame URLs, webhooks, SOAP, tax forms, KYC.
