# Validation — PR Event Gate v0.7.0

Date: 2026-09-25. Worktree tested on macOS with Python 3.11 and 3.13; only
synthetic public-safe Git histories and event payloads. CI and release checks
are recorded below after publication; a synthetic event is not proof that a
third-party repository configured a required status check correctly.

## Reproducible example

Input: a temporary base commit with `.agentic-dev-kit/policy.json` allowing
`src/`, followed by a one-line `src/app.py` fix, a mismatched event head, and
an extra `docs.md` commit. Command:

```bash
python3.11 examples/pr_event_gate_demo.py
```

Expected fixture: `examples/pr_event_gate_expected.json`. Actual output:

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 2, "rejected_reasons": [], "state": "error", "step": "wrong_checkout"}
{"exit": 1, "rejected_reasons": ["outside_scope"], "state": "rejected", "step": "outside_scope"}
```

The demo's parsed JSON exactly matched the fixture (3 cases). Its temporary
repository was removed on exit.

## Local checks

| Command | Result |
| --- | --- |
| `uv run --no-project --python 3.11 python -m unittest discover -s tests -v` | 14 tests passed |
| `uv run --python 3.13 python -m unittest discover -s tests -v` | 14 tests passed |
| `uvx ruff check .` and `uvx ruff format --check .` | Passed |
| `uvx ty check .` | Passed |
| `go run github.com/rhysd/actionlint/cmd/actionlint@latest .github/workflows/ci.yml .github/workflows/pr-event-gate.yml capabilities/workflows/pr-event-gate/caller.yml` | No diagnostics |
| `uvx bandit -q -r agentic_devkit -ll` | No medium/high findings; existing low-severity subprocess pattern outside this gate's new fixed Git calls |
| `uv build` and `uvx twine check dist/agentic_dev_kit-0.7.0*` | Wheel/sdist built; both passed metadata check |
| Isolated Python 3.13 wheel and sdist installs | `pr-event-gate --version` = `0.7.0`; installed demo returned 0/2/1 |
| `git diff --check` | Passed |

Input checks cover wrong event type, missing or malformed SHA, mismatched
checkout, duplicate event keys, oversized event, and out-of-policy change.
The workflow uses read-only permissions, no caller secrets, no candidate-code
execution, and does not use `pull_request_target`.

## Release and deployment boundary

The reusable workflow's behavior on an actual consumer PR, fork event,
required-check rule, and CODEOWNERS setup remains **unverified**; the shortest
next check is to copy `caller.yml` into a test repository with an established
base policy and open a synthetic PR. Main/tag CI and release asset verification
must be performed as part of publication; local checks do not imply either.
