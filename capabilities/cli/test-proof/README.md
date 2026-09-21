# Test Proof

Bind a test result to the exact Git state that was tested.

## Problem

A coding agent can run tests successfully and then edit the branch before handoff.
The sentence “tests passed” does not show whether the current files are still the
files that were tested. Test Proof runs an explicit command, fingerprints the Git
HEAD and tracked diff before and after it, and writes a locally verifiable receipt.

It is an evidence check, not a test framework or an AI reviewer.

[中文](README.zh-CN.md)

## Five-minute quick start

Install the toolkit with Python 3.11+ and Git:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.3.0
```

Stage new files first, then run the real project test command after `--`:

```bash
git add src/payment.py tests/test_payment.py
test-proof run . -- python -m unittest
test-proof verify .
```

The run writes `test-proof.json` under the repository's Git metadata directory.
Verification prints deterministic JSON. A valid receipt looks like:

```json
{
  "diff_matches": true,
  "head_matches": true,
  "receipt_state": "passed",
  "schema_version": 1,
  "state": "valid",
  "untracked_matches": true
}
```

After any tracked edit, staged change, commit, or new untracked file, the same
verification returns `state: "stale"` and exit `1`.

Run the disposable before/after demo:

```bash
python3.11 examples/test_proof_demo.py --installed
```

Expected and actual output:

```json
{"exit": 0, "state": "passed", "step": "run"}
{"exit": 0, "state": "valid", "step": "verify"}
{"exit": 1, "state": "stale", "step": "edit_then_verify"}
```

The checked fixture is in [`examples/test_proof_expected.json`](../../../examples/test_proof_expected.json).

## Commands and configuration

```bash
test-proof run [--receipt PATH] [REPOSITORY] -- COMMAND [ARG ...]
test-proof verify [--receipt PATH] [REPOSITORY]
```

The default receipt stays under Git metadata and does not change the working
tree. A custom receipt must be outside the working tree or inside Git metadata:

```bash
test-proof run --receipt /tmp/payment-tests.json . -- pytest -q
test-proof verify --receipt /tmp/payment-tests.json .
```

Run exit codes: `0` passed with unchanged Git state; `1` command failed; `2`
invalid input, Git, command start, or receipt I/O; `3` Git state changed while the
command ran. Verify returns `0` only for a passed receipt matching current state,
`1` for failed/changed/stale evidence, and `2` for invalid input or receipt data.

## Architecture and implementation

Test Proof uses Python's standard library and the installed Git executable:

1. Resolve the repository and current commit with fixed, read-only Git commands.
2. Hash a binary, full-index `HEAD` diff with external diff and text conversion
   disabled; count non-ignored untracked files without recording their names.
3. Reject pre-existing untracked files so new source/tests must be staged.
4. Execute the exact argument array after `--` with `shell=False`.
5. Snapshot again, atomically write a JSON receipt, and fail if state changed.
6. `verify` validates the bounded receipt schema and compares current state.

The receipt records the command arguments, result, UTC start time, duration,
commit ID, diff hashes, and untracked counts. It does not store diff contents,
filenames, command output, environment variables, or repository paths.

## Security and privacy

- The requested command is executed with the user's environment and repository as
  its working directory. Review it first. Test Proof is not a sandbox.
- No shell string is used, no model/network call is made, and no repository hook,
  external diff driver, or text conversion is invoked by the fingerprint step.
- Command arguments are stored in the receipt. Do not put tokens, passwords, or
  personal data on the command line; use the test tool's safe secret mechanism.
- Receipts can reveal a commit ID, command name, timing, and whether the working
  tree changed. Review them before publishing.
- External receipts are capped at 1 MiB and validated before use. Atomic writes
  prevent a partially written receipt from being treated as evidence.

## Limitations

- A valid receipt proves only that one command exited zero and the represented Git
  state did not change. It does not prove test quality, coverage, code correctness,
  authorship, or that a malicious command behaved honestly.
- Receipts are local JSON, not signed attestations. Anyone who can replace a
  receipt can forge it; use CI provenance or signing when adversarial trust matters.
- Ignored files and external services are not fingerprinted. Tests depending on
  mutable databases, time, network, caches, or environment may not be reproducible.
- The check does not lock the repository. A concurrent edit that changes and then
  restores the same represented state can escape detection.
- Git diff output is capped at 10 MiB. Pre-existing untracked files must be staged,
  removed, or ignored before a run.
- The local demo uses a synthetic payment change; it is near-real, not proof from
  a production repository or third-party security certification.

## Contributing

MIT licensed. See the repository [contribution guide](../../../CONTRIBUTING.md),
open an issue with a disposable Git reproduction, and never attach private code,
real credentials, or sensitive filenames. Changes to fingerprinting, receipt
validation, command execution, or exit precedence require an acceptance case.

Keywords: test evidence receipt, coding agent test verification, stale test
result, Claude Code workflow, CI evidence, Git state fingerprint, agent handoff.
