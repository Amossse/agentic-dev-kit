# Validation — v0.2.0, 2026-09-20

Local platform: macOS arm64, Python 3.11, installed Git. CI covers Ubuntu with
Python 3.11 and 3.13; its public run is the authority for remote results.

## Commands

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
python3.11 examples/range_scope_demo.py
uvx ruff check .
uvx ruff format --check agentic_devkit tests examples
uvx ty check .
uvx bandit -r agentic_devkit -ll
uv build
uvx twine check dist/*
```

## Covered behavior

- Four unittest methods pass: the existing real-index/malformed-input suites and
  new real-history/revision suites.
- A topic branch diverges, the base advances, and the candidate adds one approved
  source path plus one rejected workflow path. Only candidate paths are reported.
- Same base/head returns empty/3; source-only topic returns approved/0; missing or
  option-shaped revisions return 2 without raw repository paths.
- Repository rename detection is enabled; the CLI still reports move deletion and
  addition separately and rejects when only the new path is allowed.
- Before/after HEAD and porcelain status are equal around every CLI call.
- The disposable demo output exactly matches `range_scope_expected.json`:
  empty/3, rejected/1, approved/0.
- Ruff, formatting, ty, Bandit medium/high scan, package build, Twine metadata,
  isolated wheel/source installation and public pinned-tag execution are release
  gates. Final hashes and CI links are recorded in the release verification.

Bandit's low findings are the intentional subprocess import/fixed Git execution.
Git is resolved on PATH, commands use fixed arrays with `shell=False`, timeouts,
environment cleanup and disabled diff/textconv/fsmonitor. This is reviewed but
does not make an untrusted repository safe.

## Honest boundary

Tests use local full histories, SHA-1 repositories and ordinary single merge
bases. SHA-256 parsing is supported but not exercised. No GitHub token, live PR,
fork workflow, shallow-fetch repair, hostile object database, Windows filesystem,
multiple merge-base or criss-cross history was tested. The demo is synthetic and
near-real, not an actual provider PR. A passing range proves paths only.
