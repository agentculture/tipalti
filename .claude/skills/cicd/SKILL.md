---
name: cicd
description: >
  tipalti's CI/CD lane, layered on `agex pr`. Delegates lint / open /
  read / reply / delta to agex; adds two extensions inherited from
  steward — `status` (SonarCloud quality gate + hotspots +
  unresolved-thread tally) and `await` (read --wait + status with
  non-zero exit on Sonar ERROR or unresolved threads). Use when:
  creating PRs in tipalti, handling review feedback, polling CI status,
  or the user says "create PR", "review comments", "address feedback",
  "resolve threads". Vendored from steward's `cicd` skill (renamed from
  `pr-review` in steward 0.7.0; rebased on agex in 0.12.0). In tipalti
  this replaced the standalone `pr-review` skill.
---

# CI/CD — tipalti edition

`agex pr` (in `agentculture/agex-cli`) is the upstream for the
five core PR-lifecycle verbs — `lint`, `open`, `read`, `reply`,
`delta`. tipalti used to vendor a parallel standalone skill
(`pr-review`); this `cicd` skill replaces it by delegating those
verbs to `agex`. What's left here is **the gating layer inherited
from steward**:

- `status` — SonarCloud quality gate, OPEN issues, hotspots, deploy
  preview URL, unresolved-inline-thread tally.
- `await` — composes `agex pr read --wait` with `status` and gates on
  Sonar `ERROR` / unresolved threads. The single command to run after
  pushing a fix when you want "wake me when this PR is triage-able."

Those two are the steward-origin extensions on top of agex today.
They're filed as a feature ask upstream
([agex-cli#41](https://github.com/agentculture/agex-cli/issues/41));
once they land they migrate out of this skill.

The workflow is encapsulated in `scripts/workflow.sh` — follow that
(or call `agex pr` directly).

## Prerequisites

Hard requirements: `agex` (>=0.1), `gh` (GitHub CLI), `jq`, `bash`,
`python3` (stdlib only), `curl` (used by `pr-status.sh`).

Install agex once:

```bash
uv tool install agex-cli   # or: pip install --user agex-cli
```

Per-machine paths (sibling-project layout) live in
`.claude/skills.local.yaml`; see the committed `.example` for the
schema. `agex pr delta` reads the same file.

## How to run

`scripts/workflow.sh` is the entry point. Subcommands:

| Command | What it does |
|---------|--------------|
| `workflow.sh lint` | `agex pr lint --exit-on-violation` — portability + alignment-trigger check. |
| `workflow.sh open [gh-flags]` | `agex pr open --delayed-read`. Creates the PR, then polls 180s for an initial briefing. `--title TITLE` required; body via `--body-file PATH` or stdin. |
| `workflow.sh read [PR] [--wait N]` | `agex pr read`. One-shot briefing (CI checks, SonarCloud gate + new issues, all comments, next-step footer). Pass `--wait N` to poll up to N seconds for required reviewers. |
| `workflow.sh reply <PR>` | `agex pr reply <PR>` — batch JSONL replies (stdin) + thread resolve. agex auto-signs from `culture.yaml`, falling back to the repo basename. |
| `workflow.sh delta` | `agex pr delta` — sibling alignment dump. |
| `workflow.sh status <PR>` | **Extension.** `pr-status.sh` — Sonar gate, OPEN issues, hotspots, unresolved-thread breakdown, deploy preview URL. Authoritative gate for `await`. |
| `workflow.sh await <PR>` | **Extension.** `agex pr read --wait` then `status`. Exits non-zero on Sonar ERROR or unresolved threads. Tunables: `TIPALTI_PR_AWAIT_WAIT` (default 1800s passed to `--wait`), `TIPALTI_PR_AWAIT_SECONDS` (legacy fixed pre-sleep, deprecated). |
| `workflow.sh help` | Print the list. |

You can also call `agex pr <verb>` directly — `workflow.sh` is a
typing-saver around the same verbs. The `status` and `await`
extensions only have shell entry points.

The vendored single-comment helper `pr-reply.sh` (plus its
`_resolve-nick.sh` dependency) is still shipped — useful when a one-off
reply doesn't merit batch JSONL. It is not called by `workflow.sh`
anymore. The vendored `portability-lint.sh` is also still shipped —
`steward doctor . --scope self` runs it directly. Both are scheduled
for follow-up migration to agex.

## Long waits (background polling)

`agex pr read --wait N` polls in-session for up to N seconds. The
Anthropic prompt cache has a 5-minute TTL; sleeping past it burns
context every cache miss. Two ways to drive the wait:

- **Synchronous** — `workflow.sh await <PR>` after `gh pr create` /
  `workflow.sh open`. Fine when readiness is expected within ~5
  minutes.
- **Asynchronous** — for longer waits, run `agex pr read --wait NNN`
  inside a background subagent (Agent tool, `run_in_background: true`)
  so the main session only pays the cache cost when readiness fires.
  The subagent's only job is to invoke `agex pr read --wait` and echo
  its headline back. The parent triages with `workflow.sh await`
  when the notification arrives. The user can interrupt with
  TaskStop.

This pattern was originally borrowed from sibling repo
[`agentculture/cfafi`](https://github.com/agentculture/cfafi)'s `poll`
skill. The async guidance is also filed upstream
([agex-cli#41](https://github.com/agentculture/agex-cli/issues/41)).

## Conventions

`agex pr` emits a **"Next step:"** footer at the end of every command
that names the right next verb (the same chain `agex learn cicd`
documents) — follow that rather than memorizing an order. `workflow.sh
help` mirrors the verb table when you need the extensions (`status`,
`await`) on top.

Branch naming: `fix/<desc>`, `feat/<desc>`, `docs/<desc>`,
`skill/<name>`. PR / comment signature: `- <nick> (Claude)`, where
`<nick>` is resolved by `agex` (and by `pr-reply.sh` via
`_resolve-nick.sh`) from the agent's own `culture.yaml`, falling back
to the git-repo basename. tipalti has no `culture.yaml`, so the
signature resolves to `- tipalti (Claude)` — consistent with how the
`communicate` skill signs issue posts. The signature is auto-appended
on `pr open` / `pr reply` only when the body isn't already signed.

## Triage rules

For every comment, decide **FIX** or **PUSHBACK** with reasoning.

Default to **FIX** for: portability complaints (always valid — the
repo's no-sibling-dependency / no-`/home` rule is enforced by `steward
doctor . --scope self`), test or doc requests, style nits aligned with
workspace conventions.

Default to **PUSHBACK** for: architecture opinions that conflict with
the project `CLAUDE.md` or the all-backends rule; false-positives that
don't apply to a read-only REST explorer (e.g. "add mutation tests"
for verbs that don't mutate — defer, don't refuse).

### Alignment-delta rule

If the PR touches `CLAUDE.md`, `culture.yaml`, or anything under
`.claude/skills/`, run `workflow.sh delta` **before** declaring FIX or
PUSHBACK on each comment. Note any sibling that needs a follow-up PR
and mention it in your reply.

## Project steps

tipalti is no longer greenfield — these stack-specific steps are live
(see the project `CLAUDE.md` for the canonical commands):

```bash
uv run pytest -n auto -v                                   # test suite
python3 .claude/skills/version-bump/scripts/bump.py patch  # required on every PR
markdownlint-cli2 "**/*.md"                                 # repo-local config
```

The `version-check` CI job comments on and fails the PR if the version
matches `main`, so the bump is mandatory — no exceptions for
docs/config-only changes. A `pr lint --extra=tests,version,markdown`
ask is filed upstream
([agex-cli#41](https://github.com/agentculture/agex-cli/issues/41)).

## Reply etiquette

Every comment must get a reply — no silent fixes. `agex pr reply`
includes thread-resolve by default. Reference the review-comment IDs
in the fix-up commit message.

The `status` extension queries SonarCloud directly (it predates the
upstream Sonar integration in `agex pr read`). Both surfaces are
trustworthy — `agex pr read` for display in the briefing, `status` for
the gate. tipalti isn't a registered mesh agent (no `culture.yaml`),
so the post-merge IRC ping that Culture's PR flow includes is skipped —
that returns if tipalti joins the mesh.
