# Diff Budget

Fail an oversized coding-agent branch before it becomes a review problem.

## Problem

Path allowlists catch out-of-scope files, but an agent can still rewrite thousands
of lines inside an allowed directory. Diff Budget compares a branch from its merge
base, counts changed files and text lines, and applies explicit review budgets.

Size is only a review-cost proxy. A small diff can be dangerous and a large
mechanical change can be safe; this tool makes the policy visible, not universally
correct.

[中文](README.zh-CN.md) · [Toolkit home](../../../README.md)

## Five-minute quick start

Install Python 3.11+, Git, and the toolkit:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0
diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400
```

Exit `0` means a nonempty range is within budget; `1` means at least one budget
failed; `2` means invalid input, missing history, or Git failure; `3` means the
range is empty. JSON goes to stdout and a counts-only summary to stderr.

Run the disposable near-real example:

```bash
python3.11 examples/diff_budget_demo.py --installed
```

Actual and expected output:

```jsonl
{"changed_lines": 0, "exit": 3, "files": 0, "rejected_reasons": [], "state": "empty"}
{"changed_lines": 8, "exit": 1, "files": 2, "rejected_reasons": ["file_limit", "line_limit"], "state": "rejected"}
{"changed_lines": 2, "exit": 0, "files": 1, "rejected_reasons": [], "state": "approved"}
```

The rejected branch contains the requested two-line payment edit plus a six-line
generated file. The approved branch contains only the payment edit. The fixture is
[`examples/diff_budget_expected.json`](../../../examples/diff_budget_expected.json).

## Configuration and CI

```text
diff-budget [REPOSITORY] --base REV [--head REV]
  --max-files N --max-lines N [--max-file-lines N] [--allow-binary]
```

- `--max-files` limits all changed paths. A rename counts as a deletion and an
  addition because rename detection is deliberately disabled.
- `--max-lines` limits total additions plus deletions across text files.
- `--max-file-lines` optionally caps additions plus deletions in each text file.
- Binary files are rejected by default because Git does not expose meaningful line
  counts for them. `--allow-binary` counts them as files and zero changed lines.
- Limits are integers from `0` to `1,000,000,000`. `--head` defaults to `HEAD`.
  Revisions use the same safe single-commit contract as Range Scope.

Example GitHub pull-request job:

```yaml
- uses: actions/checkout@v5
  with:
    fetch-depth: 0
    ref: ${{ github.event.pull_request.head.sha }}
- run: pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.4.0
- run: diff-budget . --base ${{ github.event.pull_request.base.sha }} --head HEAD --max-files 20 --max-lines 600 --max-file-lines 300
```

Choose budgets from repository history and review practice rather than copying the
example. Exceptions should be explicit in the workflow or review policy, not hidden
inside generated code.

## Architecture and implementation

The stdlib implementation resolves base/head commits, computes their merge base,
and runs fixed `git diff --numstat -z --no-renames` arguments. Its NUL parser keeps
exact path bytes in base64, validates counts and framing, and distinguishes Git's
`-/-` binary records. It then returns the observed totals, every changed path, the
configured budget, and stable rejection reasons.

Git runs with `shell=False`, inherited `GIT_*` overrides removed, global/system
configuration disabled, fsmonitor off, and 10-second/10-MiB bounds. External diff,
text conversion, rename detection, fetch, checkout, commits, hooks, models, API
calls, and repository code execution are excluded.

## Security, privacy, and limitations

- Output reveals changed paths and commit IDs. Review JSON before sharing it.
- Use a trusted Git executable and repository. This is a read-only gate, not a
  sandbox for hostile Git objects or repository configuration.
- Missing, shallow, unrelated, or ambiguous history fails explicitly. The command
  does not fetch and never receives repository credentials.
- Dirty working-tree and staged-only edits are ignored. Use Staged Scope before
  commit and Range Scope when path ownership matters.
- Changed lines are additions plus deletions from Git numstat—not complexity,
  semantic risk, generated-code detection, test coverage, or reviewer effort.
- Binary files have no line count. Allowing them makes the line budget incomplete.
- Renames count both endpoints and can exceed a budget despite being mechanical.
- The gate does not split a branch, approve a PR, or decide whether an exception is
  justified. A pass proves only that the measured range fits configured numbers.
- Maximums are 10,000 records, 10 MiB captured Git output, and 10 seconds per Git
  command. The demo uses synthetic files, not production validation.

## Contribution and discovery

[Contributing](../../../CONTRIBUTING.md) · [MIT](../../../LICENSE) ·
[Changelog](../../../CHANGELOG.md) · [Research](../../../docs/research-2026-09-22.md)
· [Validation](../../../docs/validation-2026-09-22.md) ·
[Prepared launch copy](../../../PROMOTION.md).

Keywords: AI pull request size gate, coding agent diff budget, changed lines CI,
reviewable PR automation, Git numstat checker, Claude Code handoff.
