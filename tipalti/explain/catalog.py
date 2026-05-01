"""Markdown catalog for ``tipalti explain <path>``.

Each entry is verbatim markdown. Keys are command-path tuples. The empty
tuple and ``("tipalti",)`` both resolve to the root entry.

Keep bodies self-contained: an agent reading one entry should get enough
context without chaining reads.
"""

from __future__ import annotations

_ROOT = """\
# tipalti

`tipalti` is the command-line interface for Tipalti Solutions. v0.0.1
ships the agent-first affordances (`learn`, `explain`) and an auth-probe
stub (`whoami`); domain verbs that exercise the Tipalti API land in later
releases. The CLI is scaffolded from the AgentCulture sibling pattern.

## Verbs

- `tipalti learn` — structured self-teaching prompt.
- `tipalti explain <path>` — markdown docs for any noun/verb.
- `tipalti whoami` — auth probe stub (returns `unauthenticated` for now).

## Exit-code policy

- `0` success
- `1` user-input error
- `2` environment / setup error
- `3+` reserved

## See also

- `tipalti explain learn`
- `tipalti explain explain`
- `tipalti explain whoami`
"""

_LEARN = """\
# tipalti learn

Prints a structured self-teaching prompt covering tipalti's purpose,
command map, exit-code policy, `--json` support, and `explain` pointer.

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
    tipalti explain learn
    tipalti explain --json <path>
"""

_WHOAMI = """\
# tipalti whoami

Auth probe. Reports the active Tipalti principal — or
`unauthenticated` when no credentials are configured.

In v0.0.1 this is a stub: it always reports `unauthenticated` until real
Tipalti API authentication lands. Exit code is always `0` (probe, not
gate).

## Usage

    tipalti whoami
    tipalti whoami --json
"""


ENTRIES: dict[tuple[str, ...], str] = {
    (): _ROOT,
    ("tipalti",): _ROOT,
    ("learn",): _LEARN,
    ("explain",): _EXPLAIN,
    ("whoami",): _WHOAMI,
}
