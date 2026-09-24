# Policy Gate

Apply a repository policy from the base commit to a proposed coding agent branch.

## Problem

Handoff Proof lets a task creator choose `--allow` paths and size limits. In a PR,
the creator of a change should not be the only source of the policy used to check
that change. Policy Gate reads `.agentic-dev-kit/policy.json` from the selected
base commit, checks the merge-base-to-head diff, and rejects a branch that edits
the policy file in the same change.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Five-minute quick start

Requires Python 3.11+ and Git. Install the pinned toolkit:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0
```

Commit this file on your protected base branch before using the gate:

```json
{
  "schema_version": 1,
  "allow": ["src/", "tests/"],
  "max_files": 10,
  "max_lines": 400,
  "max_file_lines": 200,
  "allow_binary": false
}
```

Save it as `.agentic-dev-kit/policy.json`, then check a topic branch:

```bash
policy-gate . --base origin/main --head HEAD
```

Exit `0` approves a nonempty diff, `1` rejects it, `2` means policy/input/Git
error, and `3` means an empty diff. stdout is stable JSON; stderr is a state
summary. Missing or malformed base policy fails with `2`.

Run the disposable real Git history:

```bash
python3.11 examples/policy_gate_demo.py --installed
```

Expected and actual output:

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 1, "rejected_reasons": ["budget_exceeded"], "state": "rejected", "step": "oversized"}
{"exit": 1, "rejected_reasons": ["policy_changed", "outside_scope", "budget_exceeded"], "state": "rejected", "step": "policy_edit"}
```

The checked fixture is [`examples/policy_gate_expected.json`](../../../examples/policy_gate_expected.json).

## Configuration and CI

The JSON schema has exactly six fields. `allow` contains 1–100 literal
repository-relative files or directories ending in `/`, without globs. Numeric
limits are integers from 0 to 1,000,000,000. `max_file_lines` may be `null`.
Binary files fail unless `allow_binary` is `true`; they still count as files.
Renames count both endpoints. All thresholds should be chosen from the
repository's history and review policy.

The policy location is fixed. `--base` and `--head` are commit revisions; `HEAD`
is the default head. Use a trusted base ref. For a GitHub PR checkout:

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
    ref: ${{ github.event.pull_request.head.sha }}
- run: pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.6.0
- run: policy-gate . --base ${{ github.event.pull_request.base.sha }} --head HEAD
```

Make the CI check required through repository rules or branch protection. Protect
the policy file and the workflow with CODEOWNERS review. An intentional policy
update needs an administrator-controlled exception or separate trusted update
workflow, because this check rejects every candidate that edits the policy file.
This CLI does not set GitHub permissions.

## Architecture

1. Resolve base and head to immutable commit IDs.
2. Read at most 64 KiB of the fixed policy blob from the base commit and strictly
   validate its JSON fields. Hash the original blob for audit output.
3. Reuse Range Scope for literal path checks and Diff Budget for review-size
   checks over the same merge-base-to-head range.
4. Reject any diff containing `.agentic-dev-kit/policy.json`, even if its parent
   directory is otherwise allowed.

The runtime uses Python's standard library and fixed, read-only Git commands.
No fetch, checkout, hook, model, network request, shell string, or user code is
run by Policy Gate.

## Security, privacy, and limitations

- A caller can choose a dishonest `--base`; trust the CI event's base commit and
  require the check on the protected branch. A local run is advisory.
- The gate does not authenticate who authored or approved the base policy. Use
  branch protection, required checks, and CODEOWNERS for that trust boundary.
- A policy update needs an administrator-controlled exception or trusted update
  workflow. An ordinary PR that edits the policy file always fails this gate.
- Output contains changed paths, policy paths, commit IDs, and the policy hash.
  Review it before sharing. Do not place secrets or personal data in policy paths.
- It checks committed changes only. Dirty or staged files are ignored; use
  Staged Scope and Test Proof for local state. It does not prove correctness,
  test coverage, or semantic safety.
- A shallow checkout without the needed history fails explicitly. The tool does
  not fetch. Use a trusted Git binary and repository; this is not a sandbox.

## Contributing

MIT licensed. See [Contributing](../../../CONTRIBUTING.md),
[Changelog](../../../CHANGELOG.md), [research](../../../docs/research-2026-09-24.md),
[validation](../../../docs/validation-2026-09-24.md), and
[prepared launch copy](../../../PROMOTION.md). Submit a synthetic Git history and
the exact policy for changes to parsing or gate behavior. Do not submit secrets
or private repository paths.

Suggested topics: `agent-policy`, `coding-agents`, `claude-code`,
`code-review-automation`, `git`, `developer-tools`. Search terms: base-branch
agent policy, AI PR scope gate, policy as code for coding agents, changed-lines
budget, Claude Code review guardrail.
