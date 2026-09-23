# Handoff Proof

Turn a coding-agent completion claim into one state-bound, re-runnable handoff.

## Problem

A summary such as "changed only `src/`, stayed small, tests passed" combines three
claims that can drift independently. Reviewers must rediscover the original path
policy, size budget, test receipt, and Git state before they can trust the handoff.

Handoff Proof runs Range Scope, Diff Budget, and Test Proof together, records the
exact policy and evidence, then re-runs that policy during verification. It is a
local evidence gate, not a transcript collector, agent-memory product, or signed
supply-chain attestation.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Five-minute quick start

Install Python 3.11+, Git, and the pinned toolkit version:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0
```

Run the repository's real test command first, then create the handoff:

```bash
test-proof run . -- python -m unittest
handoff-proof create . \
  --task "Fix payment rounding" \
  --base origin/main \
  --allow src/payments/ --allow tests/ \
  --max-files 10 --max-lines 400
handoff-proof verify .
```

`create` returns `0` and writes a manifest only when all three gates approve.
The default manifest lives at `.git/agentic-dev-kit/handoff-proof.json`, so its
creation does not dirty the state proven by Test Proof. The same JSON is printed
to stdout; use `--output /tmp/handoff.json` and later
`verify --manifest /tmp/handoff.json` for an explicit portable file.

Run the disposable example:

```bash
python3.11 examples/handoff_proof_demo.py --installed
```

Expected and actual output:

```jsonl
{"exit": 1, "state": "rejected", "step": "wrong_scope"}
{"exit": 0, "state": "approved", "step": "create"}
{"exit": 0, "state": "valid", "step": "verify"}
{"exit": 1, "state": "stale", "step": "edit_then_verify"}
```

The checked output is [`examples/handoff_proof_expected.json`](../../../examples/handoff_proof_expected.json).

## Commands and configuration

```text
handoff-proof create [REPOSITORY] --task TEXT --base REV [--head REV]
  --allow PATH [--allow PATH ...] --max-files N --max-lines N
  [--max-file-lines N] [--allow-binary]
  [--test-receipt PATH] [--output PATH]

handoff-proof verify [REPOSITORY] [--manifest PATH]
```

- `--allow`, `--base`, and `--head` use Range Scope semantics.
- Numeric and binary options use Diff Budget semantics.
- `--test-receipt` selects a Test Proof receipt; omission uses its Git-metadata
  default.
- `--task` is required, nonempty, and limited to 500 characters. It is context
  for a reviewer, not a fact verified from the diff.
- `--output` and `--manifest` may select a file outside the working tree or under
  Git metadata. Working-tree destinations are rejected because they would make
  the represented test state stale.

Both commands return `0` for approved/valid, `1` for rejected/stale, and `2` for
invalid input, malformed evidence, I/O, or Git failure. Rejected creation prints
the evidence but does not overwrite the last approved manifest.

## Architecture and implementation

Handoff Proof is a deliberately thin composition layer over the toolkit's public
checks:

1. Validate the task, repository, literal allow paths, revisions, and budgets.
2. Run Range Scope against merge-base to head.
3. Run Diff Budget over the same merge-base range.
4. Verify the Test Proof receipt against the current HEAD and working state.
5. Atomically write the policy plus all three reports only if every exit is zero.
6. On `verify`, validate the bounded JSON schema and re-run the recorded policy;
   every current report must exactly match its recorded report.

The runtime remains Python standard library plus Git. It does not invoke the
three console commands through a shell; it calls their checked implementations,
preserving their fixed Git arguments, NUL-safe parsing, limits, and exit meaning.

## Security and privacy

- Handoff Proof is offline and makes no model, API, fetch, checkout, commit, or
  push call. Scope and budget checks are read-only.
- It relies on Test Proof, which executes only the command explicitly supplied
  earlier to `test-proof run`; Handoff Proof itself does not execute tests.
- The manifest contains the task text, allow paths, commit IDs, changed paths,
  size observations, and test command metadata. Review it before sharing and do
  not put secrets, personal data, or confidential task text in these fields.
- Input manifests are capped at 2 MiB and schema-validated. Writes are atomic.
- Use a trusted Git binary and repository. This is not a sandbox for hostile Git
  objects, filesystems, or concurrently mutating processes.

## Limitations

- A valid manifest proves that the three configured local checks still produce
  the recorded result. It does not prove code correctness, task completeness,
  authorship, review quality, coverage, or safe deployment.
- The task statement is asserted by the creator and is not inferred or checked.
- Manifests are unsigned local JSON. Anyone able to replace them can forge them;
  use GitHub artifact attestations, in-toto, SLSA, or signing for adversarial trust.
- Verification reuses the recorded policy. It does not prove that the policy was
  sufficiently strict or approved by the repository owner.
- Range and budget evidence covers committed merge-base-to-head changes. Test
  Proof additionally binds tracked working changes and untracked-file count.
- Ignored files, external services, environment state, and test quality remain
  outside the represented evidence.

## Contributing

MIT licensed. See the [contribution guide](../../../CONTRIBUTING.md). Include a
synthetic repository, the exact policy, expected component outcomes, and the
handoff state. Never attach private source, production paths, or credentials.

Keywords: coding agent handoff, agent evidence manifest, Claude Code workflow,
Git state proof, AI pull request gate, test receipt, review policy automation.
