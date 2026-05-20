# Design: v0.2.0 — broaden read-only REST v2 coverage

- **Date:** 2026-05-20
- **Status:** Approved (pending spec review)
- **Target version:** `0.2.0` (minor bump)
- **Topic:** Add the remaining read-only Tipalti REST v2 nouns and correct the
  API path prefix.

## Context

v0.1.0 ships a read-only explorer over three nouns — `payee`, `invoice`,
`bill` — each exposing `list` and `get` via the shared `_ResourceGroup`
(`tipalti/api/client.py`) and `register_noun_group` (`tipalti/cli/_listing.py`)
helpers. The agent-first contract holds throughout: `--json` on every verb,
markdown by default, one verb invocation = one upstream HTTP request (auth
excluded), OData `$skiptoken` pagination, single-retry on 429/5xx.

Two structural defects in the shipped code were found while scoping this work,
by checking the live REST reference (Tipalti's machine-readable docs index at
`https://documentation.tipalti.com/llms.txt`):

1. **Wrong path prefix.** The live REST API places every resource under
   `/api/v1/…` (e.g. `/api/v1/payees`). The shipped client uses `/v2/payees`,
   `/v2/invoices`, `/v2/bills` (`client.py:155-157`). The host is correct
   (`api.tipalti.com`); the path prefix is not.
2. **`bill` is not a real REST resource.** The documented API has no standalone
   `bills` collection — bills and invoices are unified under `/api/v1/invoices`.

Neither defect was caught because the resource paths have never been exercised
against the live sandbox: there is exactly one opt-in integration test, skipped
by default and not run in CI. The `/v2/` prefix and the `bill` noun are
unvalidated scaffolding.

## Goals

- Correct the resource path prefix to the documented `/api/v1/…`.
- Add the remaining read-only REST v2 nouns that fit the flat `list`/`get`
  shape, so the explorer covers the full documented read surface.
- Preserve every existing invariant (one-request, `--json`, markdown default,
  pagination, retry, error mapping).

## Non-goals / deferred

- **Mutations** (create/update/approve) — separate future release, separate spec.
- **Payment batches** (`/api/v1/payment-batches/{id}` + `/instructions`) —
  deferred. The verb/noun naming is unsettled (possibly a `batch` noun rather
  than `payment-batch`), and the get-only-plus-sub-collection shape doesn't fit
  the flat pattern. Revisit deliberately in a later release.
- **OAuth scope handling** — the token request sends no `scope` parameter
  (`auth.py:118-122`). Tipalti's client-credentials tokens are per-resource
  scoped (`tipalti.api.payment.read`, etc.). This release assumes Tipalti grants
  the client's full configured scope set when none is requested, and leaves
  `auth.py` untouched. If the new reads return 403 against the live sandbox,
  scope handling becomes its own follow-up (add an env-overridable scope
  superset, key the token cache on a scope hash).
- iFrame URL generation, webhooks, SOAP, tax forms, KYC — unchanged from
  CLAUDE.md's deferred list.

## Decisions

| Decision | Choice |
|---|---|
| Path prefix | Re-base all resource paths `/v2/` → `/api/v1/` |
| `bill` noun | **Remove outright** (no shim) — `/v2/bills` never worked |
| New nouns | `payment`, `payer-entity`, `gl-account`, `custom-field`, `payment-term`, `tax-code` (flat `list`/`get`) |
| Payment batches | Deferred |
| OAuth scopes | Left untouched; revisit only if reads 403 |

## Detailed design

### API layer — `tipalti/api/client.py`

Re-base the two surviving existing groups and register six new ones in
`TipaltiClient.__init__`. Remove the `self.bills` group.

```python
self.payees         = _ResourceGroup(self, "/api/v1/payees",         "payee")
self.invoices       = _ResourceGroup(self, "/api/v1/invoices",       "invoice")
self.payments       = _ResourceGroup(self, "/api/v1/payments",       "payment")
self.payer_entities = _ResourceGroup(self, "/api/v1/payer-entities", "payer-entity")
self.gl_accounts    = _ResourceGroup(self, "/api/v1/gl-accounts",    "gl-account")
self.custom_fields  = _ResourceGroup(self, "/api/v1/custom-fields",  "custom-field")
self.payment_terms  = _ResourceGroup(self, "/api/v1/payment-terms",  "payment-term")
self.tax_codes      = _ResourceGroup(self, "/api/v1/tax-codes",      "tax-code")
```

`whoami` continues to probe `/v2/me` → re-base to `/api/v1/me` and confirm the
documented probe path (the docs index does not list a dedicated `me`
resource; if `/api/v1/me` is absent, fall back to a cheap `payees` list with
`$top=1` as the probe, preserving the `unauthenticated`-on-401 semantics).
**Open implementation detail — resolve during the plan by checking the live
reference; do not guess the path silently.**

No other change to `_ResourceGroup`, `_normalize_envelope`, retry, or error
mapping — the new nouns are pure reuse.

### CLI layer — `tipalti/cli/_commands/`

One module per new noun, each ~15 lines mirroring `payee.py`, wired through
`register_noun_group`. CLI noun names are kebab-case to match the resource
paths; client attribute names are the underscored plurals.

| Module | CLI noun | Client attr | List columns (initial best-guess; refine against live payloads) |
|---|---|---|---|
| `payment.py` | `payment` | `payments` | `id, refCode, status, amount, currency` |
| `payer_entity.py` | `payer-entity` | `payer_entities` | `id, name, status` |
| `gl_account.py` | `gl-account` | `gl_accounts` | `id, name, code` |
| `custom_field.py` | `custom-field` | `custom_fields` | `id, name, type` |
| `payment_term.py` | `payment-term` | `payment_terms` | `id, name, days` |
| `tax_code.py` | `tax-code` | `tax_codes` | `id, name, rate` |

List columns are render-only (markdown table headers); unknown keys render
blank, so a wrong guess degrades gracefully and is cheap to correct. The plan
should refine columns against real sandbox payloads where available.

Register the six new modules in `tipalti/cli/__init__._build_parser` and
**remove** the `bill` import and `_bill_cmd.register(sub)` line.

Delete `tipalti/cli/_commands/bill.py`.

### explain catalog — `tipalti/explain/catalog.py`

- Add entries for each new noun and its `list`/`get` verbs, following the
  existing `_PAYEE` / `_PAYEE_LIST` / `_PAYEE_GET` shape.
- Remove the `_BILL`, `_BILL_LIST`, `_BILL_GET` entries and their `ENTRIES` keys.
- Update `_ROOT`'s "Verbs" and "See also" lists; refresh the `learn` copy
  (`tipalti/cli/_commands/learn.py`) to cover the new nouns and drop `bill`.
- Update the `_AUTH` entry only if the path correction changes any documented
  default (it does not — only the per-resource prefix changes, which `explain`
  does not enumerate).

### Tests — `tests/`

TDD throughout (write failing test, then implement). Mirror the existing split:

- New per-noun CLI test modules: `test_cli_payment.py`, `test_cli_payer_entity.py`,
  `test_cli_gl_account.py`, `test_cli_custom_field.py`, `test_cli_payment_term.py`,
  `test_cli_tax_code.py` — each covering `list` (markdown + `--json` envelope,
  pagination cursor passthrough) and `get` (markdown + `--json`, 404 → exit 1),
  modeled on `test_cli_payee.py`.
- `test_api_client.py`: assert each new group hits the correct `/api/v1/…`
  path; add a regression test asserting **every** registered resource path
  starts with `/api/v1/`.
- **Remove** `tests/test_cli_bill.py`; add a smoke assertion that
  `tipalti bill` is rejected (argparse invalid-choice → exit 1).
- Update `test_cli_smoke.py` if it enumerates the noun set.
- The opt-in `@pytest.mark.integration` test stays skipped; optionally extend it
  to read one new endpoint, still gated on live creds.

### Versioning & docs

- `python3 .claude/skills/version-bump/scripts/bump.py minor` → `0.2.0`.
- CHANGELOG: **Added** (6 nouns), **Changed** (resource path prefix `/v2/` →
  `/api/v1/`), **Removed** (`bill` noun + verbs).
- Update CLAUDE.md: Status line, the noun list under "What this project is",
  and the `cli/_commands/` tree in "Project shape".

## Invariants preserved

- One verb = one HTTP request (auth excluded) — every new verb is a single
  `list`/`get`.
- `--json` everywhere, markdown default, OData `$skiptoken` pagination,
  single-retry on 429/5xx, `AfiError` mapping — all unchanged.
- `steward doctor . --scope self` portability + skills contract — unaffected.

## File-by-file change summary

**Modified**

- `tipalti/api/client.py` — re-base paths, drop `bills`, add 6 groups.
- `tipalti/cli/__init__.py` — register 6 modules, drop `bill`.
- `tipalti/explain/catalog.py` — add new entries, drop bill entries, update root.
- `tipalti/cli/_commands/learn.py` — refresh copy.
- `tests/test_api_client.py` — path assertions + prefix regression guard.
- `tests/test_cli_smoke.py` — noun-set updates if enumerated.
- `pyproject.toml`, `CHANGELOG.md` — version bump.
- `CLAUDE.md` — status + noun list + tree.

**Added**

- `tipalti/cli/_commands/{payment,payer_entity,gl_account,custom_field,payment_term,tax_code}.py`
- `tests/test_cli_{payment,payer_entity,gl_account,custom_field,payment_term,tax_code}.py`

**Removed**

- `tipalti/cli/_commands/bill.py`
- `tests/test_cli_bill.py`
