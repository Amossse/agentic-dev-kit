# Range Scope

Gate a committed coding-agent branch against explicit file and directory scopes.
[中文](README.zh-CN.md) · [Toolkit home](../../../README.md)

## Problem

A PR can contain the requested payment fix and an unrelated workflow edit. CI
needs the paths introduced by the candidate branch, even if the base branch has
advanced since the branch diverged. GitHub displays PR changes from that
divergence point; Range Scope applies a deterministic literal allowlist to the
same merge-base-to-head shape without calling GitHub or a model.

## Install and five-minute quick start

Requires Python 3.11+ and Git. There are no runtime package dependencies.

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0
range-scope . --base origin/main --head HEAD --allow src/payments/ --allow tests/
```

Exit `0` means a nonempty approved range; `1` means an outside-scope path; `2`
means invalid input, missing history or Git failure; `3` means no changed paths.
JSON goes to stdout and a counts-only summary to stderr.

Reproduce all three outcomes in a disposable repository:

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/range_scope_demo.py --installed
```

Actual and expected output:

```jsonl
{"changed_records": 0, "exit": 3, "rejected_paths": [], "state": "empty"}
{"changed_records": 2, "exit": 1, "rejected_paths": [".github/workflows/ci.yml"], "state": "rejected"}
{"changed_records": 1, "exit": 0, "rejected_paths": [], "state": "approved"}
```

The rejected branch changes `src/payment.py` and `.github/workflows/ci.yml`.
The approved branch contains only the payment change. The demo asserts the real
subprocess exits and JSON; its expected rows are in
[`range_scope_expected.json`](../../../examples/range_scope_expected.json).

## Configuration and CI

```text
range-scope [REPOSITORY] --base REV [--head REV] --allow PATH [--allow PATH ...]
```

`--head` defaults to `HEAD`. Revisions resolve to commits before diffing. A
revision is at most 512 characters and cannot start with `-`, contain whitespace,
controls, `..`, or `...`. Range expressions are deliberately rejected; the tool
constructs one comparison itself.

Allow rules are shared with Staged Scope: a trailing slash is a literal directory
prefix, otherwise the whole Git path must match. Rules are case-sensitive UTF-8
bytes, not globs. See the [complete path contract](../staged-scope/README.md#configuration-and-exact-contract).

For GitHub pull requests, fetch complete history and check the actual head SHA,
not the synthetic merge commit:

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
    ref: ${{ github.event.pull_request.head.sha }}
- run: pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0
- run: range-scope . --base ${{ github.event.pull_request.base.sha }} --head HEAD --allow src/ --allow tests/
```

Pin third-party actions and this package according to your supply-chain policy.
For fork PRs, checkout and execute only trusted base-branch workflow code. This
tool does not execute files from the candidate branch, but a workflow may do so
in other steps.

## Implementation

The stdlib implementation resolves both revisions with `git rev-parse --verify
--end-of-options`, computes `git merge-base BASE HEAD`, then runs a fixed
`git diff --name-status -z --no-renames` from that commit to HEAD. Disabling
rename detection means both the deletion and addition path of a move must pass.
The JSON includes resolved base, head and merge-base object IDs.

The existing NUL parser, byte-safe filename output, allow validation, fixed Git
runner, record limits and deterministic report are reused from Staged Scope.
Commands use `shell=False`, clear inherited `GIT_*` overrides, disable global and
system Git config, fsmonitor, external diff and text conversion, and time out
after 10 seconds. The CLI performs no fetch, checkout, commit or network call.

## Security, privacy and limits

- Use a trusted Git executable and repository. This is a read-only evidence gate,
  not a sandbox for a malicious object database or repository configuration.
- Output reveals changed paths and commit hashes. Review it before publishing.
- Missing/shallow history or unrelated histories fail explicitly with exit `2`;
  fetch policy and credentials remain outside this tool.
- It models PR-style merge-base-to-head changes. It does not model GitHub push
  event two-dot rules, stacked PR policy, multiple merge bases or merge results.
- Dirty working-tree and staged-only changes are ignored. Use Staged Scope before
  commit. Changed submodule gitlinks are paths; submodule contents are not read.
- A pass proves only observed paths, not authorship, safe contents, tests,
  approvals, code ownership or the future state of mutable branch names.
- Maximums are 100 allow rules, 10000 status records, 10 MiB captured Git output
  and 10 seconds per Git command. Output size is checked after capture.

## Contribution and discovery

[Contributing](../../../CONTRIBUTING.md) · [MIT](../../../LICENSE) ·
[Changelog](../../../CHANGELOG.md) · [Research](../../../docs/research-2026-09-20.md)
· [Validation](../../../docs/validation-2026-09-20.md) ·
[Prepared launch copy](../../../PROMOTION.md).

Keywords: pull request path scope, coding agent CI gate, Git merge-base checker,
Claude Code branch guard, agentic workflow evidence.
