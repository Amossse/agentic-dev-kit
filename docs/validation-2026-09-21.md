# Validation — v0.3.0, 2026-09-21

Local platform: macOS arm64, Python 3.11, installed Git. CI covers Ubuntu with
Python 3.11 and 3.13; the public run is authoritative after release.

## Commands

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
python3.11 examples/range_scope_demo.py
python3.11 examples/test_proof_demo.py
uvx ruff check .
uvx ruff format --check agentic_devkit tests examples
uvx ty check .
uvx bandit -r agentic_devkit -ll
uv build
uvx twine check dist/*
```

Release-only checks also install wheel and source distributions into separate
temporary environments, run every console `--version`, execute Test Proof through
the installed wheel, scan source/docs/build metadata for credentials and private
identifiers, push the tagged commit, and verify the public release assets/hashes.

## Covered behavior

- Six unittest methods pass, including a real temporary Git repository for Test
  Proof plus all Staged Scope and Range Scope acceptance checks.
- A staged payment edit runs a passing Python assertion, writes a receipt in Git
  metadata, and verifies as `valid`/exit `0` without changing HEAD or worktree.
- Editing the tracked file after the run produces `stale`/exit `1`.
- A command that changes tracked state returns exit `3`; a failing command returns
  exit `1` and leaves a non-valid receipt; pre-existing untracked input returns an
  explicit exit `2` diagnostic.
- The disposable demo output matches `test_proof_expected.json`: passed run,
  valid verification, then stale verification after an edit.
- Ruff lint/format, ty, Bandit medium/high scan, package build, Twine metadata,
  isolated installs, public pinned-tag commands and CI are release gates.

## Security review

The fingerprint path reuses sanitized fixed Git execution with system/global Git
config disabled, a 10-second Git timeout and 10 MiB output bound. Diff uses
`--binary`, `--full-index`, `--no-renames`, `--no-ext-diff`, `--no-textconv`, and
explicit `HEAD --`. The requested test command uses an argument array and
`shell=False`; it intentionally inherits the user's environment and is therefore
an execution boundary, not a sandbox. Receipt reads are capped at 1 MiB and schema
validated; writes are atomic.

## Honest boundary

Tests cover an ordinary SHA-1 repository and local Python commands. SHA-256 IDs are
accepted but not exercised. There is no Windows matrix, hostile Git object store,
submodule fixture, concurrent writer stress test, signal/timeout control, signed
attestation, remote CI provider, or external-service reproducibility proof. Ignored
files are outside the fingerprint. The synthetic demo does not establish test
quality or third-party security certification.
