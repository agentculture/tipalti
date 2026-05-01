"""Markdown catalog for ``tipalti explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty
tuple and ``("tipalti",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# tipalti

`tipalti` is the command-line interface for Tipalti Solutions. v0.1.0
ships a read-only explorer over Tipalti's REST v2 API (Payees, Invoices,
Bills) plus the agent-first affordances (`learn`, `explain`, `whoami`).

The CLI is scaffolded from the AgentCulture sibling pattern. Its primary
consumer is an LLM agent: every verb supports `--json`, errors carry
machine-readable remediations, and one verb invocation = one upstream
HTTP request.

## Verbs

- `tipalti learn` — structured self-teaching prompt.
- `tipalti explain <path>` — markdown docs for any noun/verb.
- `tipalti whoami` — auth probe (returns `unauthenticated` and exits 0
  when no credentials are configured).
- `tipalti payee list` / `tipalti payee get <id>` — payees (read-only).
- `tipalti invoice list` / `tipalti invoice get <id>` — invoices.
- `tipalti bill list` / `tipalti bill get <id>` — bills.

## Authentication

See `tipalti explain auth`.

## Exit-code policy

- `0` success
- `1` user-input error (bad flag, bad path, API 4xx)
- `2` environment / setup error (missing env vars, transport failure)
- `3+` reserved

## See also

- `tipalti explain learn`
- `tipalti explain explain`
- `tipalti explain whoami`
- `tipalti explain payee`
- `tipalti explain invoice`
- `tipalti explain bill`
- `tipalti explain auth`
"""

_LEARN = """\
# tipalti learn

Prints a structured self-teaching prompt covering tipalti's purpose,
command map, env vars, exit-code policy, `--json` support, pagination
model, and `explain` pointer.

## Usage

    tipalti learn
    tipalti learn --json
"""

_EXPLAIN = """\
# tipalti explain <path>

Prints markdown documentation for any noun/verb path. Unlike `--help`
(terse, positional), `explain` is global and addressable by path.

## Usage

    tipalti explain tipalti
    tipalti explain auth
    tipalti explain payee
    tipalti explain payee list
    tipalti explain --json <path>
"""

_WHOAMI = """\
# tipalti whoami

Probes the active Tipalti principal using credentials from the env vars
documented in `tipalti explain auth`.

When no credentials are configured, when `TIPALTI_CLIENT_ID/SECRET` are
empty, or when the token endpoint returns 401, `whoami` reports
`unauthenticated` and exits `0` (probe, not gate). Other API/transport
errors propagate normally with `EXIT_USER_ERROR` / `EXIT_ENV_ERROR`.

## Usage

    tipalti whoami
    tipalti whoami --json
"""

_AUTH = """\
# Authentication

Tipalti REST v2 uses OAuth 2.0 client credentials. The CLI reads:

| Env var                 | Purpose                                   | Required |
|-------------------------|-------------------------------------------|----------|
| `TIPALTI_CLIENT_ID`     | OAuth2 client ID                          | yes      |
| `TIPALTI_CLIENT_SECRET` | OAuth2 client secret                      | yes      |
| `TIPALTI_ENV`           | `sandbox` \\| `production` (default: sandbox) | no   |
| `TIPALTI_API_BASE`      | Override the API base URL for the env     | no       |
| `TIPALTI_TOKEN_URL`     | Override the OAuth2 token URL for the env | no       |

Default URLs:

- Sandbox API:   `https://api.sandbox.tipalti.com`
- Production API: `https://api.tipalti.com`
- Token URL: `<API base>/oauth2/token`

If the published Tipalti URLs ever differ from these defaults (e.g. for
the Procurement REST surface), set `TIPALTI_API_BASE` and
`TIPALTI_TOKEN_URL` explicitly — no code change needed.

## Token cache

Bearer tokens are cached at `$XDG_CACHE_HOME/tipalti/token-<env>.json`
(falls back to `$HOME/.cache/tipalti/...`), file mode `0600`. The cache is a
pure performance optimization: delete the file to force re-authentication.
The cache is automatically invalidated when `TIPALTI_CLIENT_ID` rotates.

## Diagnostics

    tipalti whoami         # is auth working?
    tipalti whoami --json  # principal payload
"""

_PAYEE = """\
# tipalti payee

Read-only verbs over Tipalti's Payees resource (REST v2).

## Verbs

- `tipalti payee list` — list payees with optional `--filter`, `--limit`,
  `--cursor`. One HTTP request per call. JSON envelope:
  `{"items": [...], "next_cursor": str|null}`.
- `tipalti payee get <id>` — fetch one payee by id.

## Usage

    tipalti payee list --limit 50
    tipalti payee list --filter "status eq 'Active'"
    tipalti payee list --cursor <token-from-prior-list>
    tipalti payee get <id>
    tipalti payee get <id> --json
"""

_PAYEE_LIST = """\
# tipalti payee list

Lists payees from Tipalti REST v2. One HTTP request per invocation.

## Flags

- `--limit N` — max records (default 100, max 500).
- `--cursor TOKEN` — continuation token from a prior list response.
- `--filter STR` — server-side filter, forwarded raw as `$filter`.
- `--json` — emit `{"items": [...], "next_cursor": str|null}`.

## Examples

    tipalti payee list --limit 25
    tipalti payee list --filter "status eq 'Active'"
    tipalti payee list --json --filter "country eq 'US'"
"""

_PAYEE_GET = """\
# tipalti payee get <id>

Fetches a single payee by id from Tipalti REST v2.

## Flags

- `--json` — emit the raw API record.

## Errors

- `1` `not found: payee <id>` when the API returns 404.
- `1` `tipalti auth failed` on 401.
- `2` `cannot reach tipalti: ...` on transport failure.
"""

_INVOICE = """\
# tipalti invoice

Read-only verbs over Tipalti's Invoices resource (REST v2).

## Verbs

- `tipalti invoice list` — list invoices with optional `--filter`,
  `--limit`, `--cursor`.
- `tipalti invoice get <id>` — fetch one invoice by id.

## Usage

    tipalti invoice list --limit 50
    tipalti invoice list --filter "status eq 'Approved'"
    tipalti invoice get <id>
"""

_INVOICE_LIST = """\
# tipalti invoice list

Lists invoices from Tipalti REST v2. Same flag set as `tipalti payee list`:
`--limit`, `--cursor`, `--filter`, `--json`. One HTTP request per call.

## Examples

    tipalti invoice list --filter "status eq 'Approved'"
    tipalti invoice list --json --limit 200
"""

_INVOICE_GET = """\
# tipalti invoice get <id>

Fetches a single invoice by id. `--json` emits the raw API record.
"""

_BILL = """\
# tipalti bill

Read-only verbs over Tipalti's Bills resource (REST v2).

## Verbs

- `tipalti bill list` — list bills with optional `--filter`, `--limit`,
  `--cursor`.
- `tipalti bill get <id>` — fetch one bill by id.

## Usage

    tipalti bill list --limit 50
    tipalti bill list --filter "status eq 'Open'"
    tipalti bill get <id>
"""

_BILL_LIST = """\
# tipalti bill list

Lists bills from Tipalti REST v2. Same flag set as `tipalti payee list`:
`--limit`, `--cursor`, `--filter`, `--json`. One HTTP request per call.
"""

_BILL_GET = """\
# tipalti bill get <id>

Fetches a single bill by id. `--json` emits the raw API record.
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("tipalti",): _ROOT,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("whoami",): _WHOAMI,
    ("auth",): _AUTH,
    ("payee",): _PAYEE,
    ("payee", "list"): _PAYEE_LIST,
    ("payee", "get"): _PAYEE_GET,
    ("invoice",): _INVOICE,
    ("invoice", "list"): _INVOICE_LIST,
    ("invoice", "get"): _INVOICE_GET,
    ("bill",): _BILL,
    ("bill", "list"): _BILL_LIST,
    ("bill", "get"): _BILL_GET,
}
