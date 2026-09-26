# Changelog

## 0.8.0 — 2026-09-26

- Add Required Check Audit, a read-only GitHub branch-protection check for the
  exact PR Event Gate status context, with offline snapshots and explicit 404
  uncertainty.
- Document ruleset and bypass limits, include bilingual quick starts, fixtures,
  acceptance test, research and validation records, and unposted launch copy.

## 0.7.0 — 2026-09-25

- Add PR Event Gate, a GitHub `pull_request` event-to-policy CLI and reusable
  workflow that binds checked-out HEAD to event head SHA before reusing Policy Gate.
- Reject unsupported events, malformed/oversized JSON and SHA mismatch; include
  synthetic Git acceptance tests, bilingual workflow docs, caller example,
  security boundaries, research, validation evidence and unposted launch copy.

## 0.6.0 — 2026-09-24

- Add Policy Gate: load a strict JSON policy from the selected base commit,
  enforce path and review-size limits, and reject policy edits in the candidate.
- Reuse Range Scope and Diff Budget with resolved commit IDs; add bilingual docs,
  a real Git before/after fixture, acceptance tests, safety boundaries, research,
  validation evidence, and prepared launch copy.

## 0.5.0 — 2026-09-23

- Add Handoff Proof to compose Range Scope, Diff Budget and Test Proof into one
  state-bound, re-runnable coding-agent handoff manifest.
- Reject failed component evidence, keep manifests outside the working tree,
  atomically write approved evidence, and detect later Git-state drift.
- Add bilingual documentation, a rejected/valid/stale fixture, acceptance tests,
  trend research, security boundaries, validation evidence and launch copy.

## 0.4.0 — 2026-09-22

- Add Diff Budget for merge-base-to-head file, total-line, per-file-line, and
  binary-file review budgets.
- Reuse safe revision resolution and fixed Git execution; add NUL-safe numstat
  parsing, conservative rename accounting, stable JSON and explicit exit codes.
- Add bilingual documentation, a disposable oversized-branch fixture, acceptance
  tests, trend research, validation evidence, security boundaries and launch copy.

## 0.3.0 — 2026-09-21

- Add Test Proof to run an explicit test command and bind its result to Git HEAD
  plus a tracked-diff fingerprint.
- Reject pre-existing untracked files, detect repository changes during tests,
  atomically write bounded JSON receipts, and fail verification after later edits.
- Add bilingual documentation, a disposable before/after demo, acceptance tests,
  trend research, validation evidence, security boundaries and launch copy.

## 0.2.0 — 2026-09-20

- Add Range Scope for read-only merge-base-to-head path gates in PR and CI flows.
- Reuse Staged Scope's literal path validation, NUL-safe records, deterministic
  JSON, fixed Git execution and exit-code contract.
- Add bilingual docs, divergent-history and rename fixtures, CI example,
  research, validation evidence and prepared launch copy.

## 0.1.0 — 2026-09-16

- Establish the Agentic Dev Kit main installation and contribution entry point.
- Add Staged Scope: read-only Git index gate with literal paths, rename endpoints,
  unmerged rejection, deterministic JSON and explicit empty-index exit.
- Include bilingual capability docs, disposable before/after example, real Git
  acceptance checks, research, launch copy and release validation.
