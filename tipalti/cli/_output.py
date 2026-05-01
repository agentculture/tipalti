"""stdout / stderr helpers with a strict split (stable-contract).

Rule: **results go to stdout, diagnostics and errors go to stderr.** Agents
parsing output can rely on this invariant. JSON mode routes structured
payloads to the same streams — never mixes them.

Default human-mode output is markdown (heading + key/value list or table).
The render helpers (:func:`render_record_md`, :func:`render_list_md`,
:func:`render_kv_md`) produce strings that are then handed to
:func:`emit_result` — they don't write directly.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Mapping, Sequence, TextIO

from tipalti.cli._errors import AfiError


def emit_result(data: Any, *, json_mode: bool, stream: TextIO | None = None) -> None:
    """Write a command result to stdout (or ``stream``)."""
    s = stream if stream is not None else sys.stdout
    if json_mode:
        json.dump(data, s, ensure_ascii=False)
        s.write("\n")
        return
    text = data if isinstance(data, str) else str(data)
    s.write(text)
    if not text.endswith("\n"):
        s.write("\n")


def emit_error(err: AfiError, *, json_mode: bool, stream: TextIO | None = None) -> None:
    """Write an :class:`AfiError` to stderr.

    Text mode renders as two lines when a remediation is present::

        error: <message>
        hint: <remediation>

    The ``hint:`` prefix is required by the agent-first error rubric.
    """
    s = stream if stream is not None else sys.stderr
    if json_mode:
        json.dump(err.to_dict(), s, ensure_ascii=False)
        s.write("\n")
        return
    s.write(f"error: {err.message}\n")
    if err.remediation:
        s.write(f"hint: {err.remediation}\n")


def emit_diagnostic(message: str, *, stream: TextIO | None = None) -> None:
    """Write a human diagnostic (progress, summary) to stderr."""
    s = stream if stream is not None else sys.stderr
    s.write(message if message.endswith("\n") else message + "\n")


# ---- markdown render helpers ------------------------------------------------


def _scalar_md(value: Any) -> str:
    """Render a scalar for inline use in a markdown bullet."""
    if value is None:
        return "_null_"
    if isinstance(value, bool):
        return "`true`" if value else "`false`"
    if isinstance(value, (int, float)):
        return f"`{value}`"
    text = str(value)
    if "\n" in text or len(text) > 80:
        return "\n\n" + _fenced_json(text) + "\n"
    return text


def _fenced_json(blob: Any) -> str:
    if isinstance(blob, str):
        return f"```\n{blob}\n```"
    return "```json\n" + json.dumps(blob, indent=2, ensure_ascii=False) + "\n```"


def render_kv_md(title: str, fields: Mapping[str, Any]) -> str:
    """Render ``title`` + a flat key/value bullet list. Used by ``whoami``."""
    lines = [f"# {title}", ""]
    for key, value in fields.items():
        lines.append(f"- **{key}:** {_scalar_md(value)}")
    return "\n".join(lines) + "\n"


def render_record_md(title: str, record: Mapping[str, Any] | Any) -> str:
    """Render a single resource record as markdown.

    Top-level scalar fields → bullet list. Nested objects/arrays → fenced
    JSON blocks under a sub-heading. Non-mapping records (string, list)
    are rendered as a single fenced JSON block.
    """
    if not isinstance(record, Mapping):
        return f"# {title}\n\n{_fenced_json(record)}\n"

    scalar_lines: list[str] = []
    nested: list[tuple[str, Any]] = []
    for key, value in record.items():
        if isinstance(value, (Mapping, list)):
            nested.append((key, value))
        else:
            scalar_lines.append(f"- **{key}:** {_scalar_md(value)}")

    parts = [f"# {title}", ""]
    if scalar_lines:
        parts.extend(scalar_lines)
        parts.append("")
    for key, value in nested:
        parts.append(f"## {key}")
        parts.append("")
        parts.append(_fenced_json(value))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def render_list_md(
    title: str,
    items: Sequence[Mapping[str, Any]],
    columns: Sequence[str],
    *,
    next_cursor: str | None,
    next_command: str | None = None,
) -> str:
    """Render an ``{"items", "next_cursor"}`` list envelope as markdown.

    ``columns`` is the ordered list of field names to project into the
    table. Missing fields are rendered as an empty cell. Non-scalar values
    are JSON-encoded inline.
    """
    parts = [f"## {title}", ""]
    if not items:
        parts.append("_No results._")
        if next_cursor and next_command:
            parts.append("")
            parts.append(f"**Next page:** `{next_command} --cursor={next_cursor}`")
        return "\n".join(parts) + "\n"

    parts.append("| " + " | ".join(columns) + " |")
    parts.append("| " + " | ".join(["---"] * len(columns)) + " |")
    for row in items:
        cells = [_table_cell(row.get(col) if isinstance(row, Mapping) else None) for col in columns]
        parts.append("| " + " | ".join(cells) + " |")

    parts.append("")
    if next_cursor and next_command:
        parts.append(f"**Next page:** `{next_command} --cursor={next_cursor}`")
    else:
        parts.append("_End of results._")
    return "\n".join(parts) + "\n"


def _table_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (Mapping, list)):
        encoded = json.dumps(value, ensure_ascii=False)
        if len(encoded) > 60:
            encoded = encoded[:57] + "..."
        return f"`{encoded}`"
    text = str(value).replace("|", "\\|").replace("\n", " ")
    return text
