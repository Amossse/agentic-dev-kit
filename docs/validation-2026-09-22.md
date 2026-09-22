# Validation — v0.4.0, 2026-09-22

Local platform: macOS arm64, Python 3.11, installed Git. CI covers Ubuntu with
Python 3.11 and 3.13; its public run is authoritative after release.

## Commands

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
python3.11 examples/range_scope_demo.py
python3.11 examples/test_proof_demo.py
python3.11 examples/diff_budget_demo.py
uvx ruff check .
uvx ruff format --check agentic_devkit tests examples
uvx ty check .
uvx bandit -r agentic_devkit -ll
uv build
uvx twine check dist/*
```

Release gates also install wheel and source distributions in separate temporary
environments, execute every console `--version`, run the installed Diff Budget
demo, scan changed source/docs/metadata for credentials and private identifiers,
push the tag, verify public CI, and compare downloaded release-asset hashes.

## Covered behavior

- Eight unittest methods pass, including real temporary Git histories for all four
  capabilities.
- A branch with a two-line payment edit plus six-line generated file exceeds both
  one-file and four-line budgets; the payment-only branch passes.
- Base-branch changes after divergence do not enter candidate totals; equal
  base/head returns empty/exit `3`.
- A NUL-containing binary fixture is rejected by default and passes only with
  `--allow-binary`; it counts as a file and zero text lines.
- Enabling repository rename detection does not change the result: a move counts
  deletion and addition separately and can exceed the file budget.
- The optional per-file line limit rejects a file even when aggregate limits pass.
- Negative/oversized limits and malformed/incomplete numstat framing fail
  explicitly; the CLI does not change HEAD, index, or working tree.
- The disposable demo output structurally matches `diff_budget_expected.json`.
- Ruff lint/format, ty, Bandit medium/high scan, package build, Twine metadata,
  isolated installs, pinned-tag execution, asset hashes, and CI are release gates.

## Security review

Diff Budget reuses sanitized fixed Git execution with system/global configuration
disabled, inherited `GIT_*` variables removed, fsmonitor off, 10-second timeout,
and 10-MiB capture limit. The diff disables rename detection, external diff and
textconv; no shell, fetch, checkout, model, API, hook, or repository code runs.
Input revisions and numeric limits are bounded, and NUL records plus path/count
fields are validated before JSON emission.

## Honest boundary

Tests cover ordinary SHA-1 repositories, text edits, one binary file, a base
advance, and a rename. SHA-256 IDs are accepted but not exercised. There is no
Windows matrix, hostile object database, submodule fixture, multiple merge-base or
criss-cross history, massive-output stress test, generated-file classifier, glob
exclusion, semantic risk model, or proof that a chosen budget improves review.
