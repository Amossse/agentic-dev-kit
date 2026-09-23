# Validation — 2026-09-23

Target: Agentic Dev Kit 0.5.0, Handoff Proof. Local platform: macOS arm64;
release CI additionally covers Linux with Python 3.11 and 3.13.

## Acceptance and end-to-end behavior

```bash
python3.11 -m unittest discover -s tests -v
```

Result: 10/10 test methods passed. New acceptance coverage uses disposable real
Git histories and the public CLIs to verify:

- a failed Range Scope component returns `rejected` and writes no manifest;
- an approved committed change with current Test Proof creates a manifest;
- immediate verification returns `valid`;
- a later tracked edit returns `stale` and specifically invalidates test evidence;
- a malformed external manifest returns exit `2` without a traceback;
- repository paths are not emitted in the checked output.

```bash
python3.11 examples/handoff_proof_demo.py \
  | diff -u examples/handoff_proof_expected.json -
```

Result: exact match. Actual output:

```jsonl
{"exit": 1, "state": "rejected", "step": "wrong_scope"}
{"exit": 0, "state": "approved", "step": "create"}
{"exit": 0, "state": "valid", "step": "verify"}
{"exit": 1, "state": "stale", "step": "edit_then_verify"}
```

All four earlier demos also passed unchanged.

## Static and security checks

```bash
uvx ruff check .
uvx ruff format --check .
uvx ty check .
uvx bandit -q -r agentic_devkit -ll
git diff --check
```

Result: lint, format, type check and whitespace checks passed. Bandit reported no
medium/high finding. The full scan reported four expected low findings for the
shared fixed-argument subprocess implementation (`B404`/`B603`); no shell string
is used. A targeted scan found no ByteDance/internal identifiers, TQS values,
AWS-key pattern, or GitHub-token pattern in the new source, docs, fixture or tests.

## Package and isolated installation

```bash
uv build
uvx twine check dist/*
```

Result: created and validated:

- `agentic_dev_kit-0.5.0-py3-none-any.whl`
- `agentic_dev_kit-0.5.0.tar.gz`

Each artifact was installed into a separate temporary Python 3.13 environment.
In both environments:

```text
handoff-proof --version  -> 0.5.0
python examples/handoff_proof_demo.py --installed -> exact expected-output match
```

Runtime dependencies remain empty; Python 3.11+ and Git are required.

## Boundary of this evidence

Local checks establish behavior and package installability on the recorded
machine. They do not establish Linux CI, remote tag parity, or public release
availability. Those are verified separately after push and release, and their
links are added to the release report rather than retroactively claimed here.
