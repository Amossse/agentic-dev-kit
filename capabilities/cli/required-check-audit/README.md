# Required Check Audit

Read a GitHub branch-protection snapshot and verify that the PR Event Gate's
actual check context is required for merges.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Problem and five-minute start

A green PR Event Gate run is advisory until the target branch requires its check.
After enabling branch protection, copy the exact check name from a PR's Checks
tab and run:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.8.0
required-check-audit OWNER/REPO --branch main --check 'policy'
```

This read-only command uses an authenticated `gh api` request. Run `gh auth login`
first if needed. It returns `0` when the exact name appears in branch protection,
`1` when the returned protection omits it, and `2` for invalid input, failed API
access, or malformed JSON. A GitHub 404 is **not** proof of missing protection:
it can also mean insufficient access, so the tool returns `2`.

Offline before/after reproduction, requiring only Python 3.11+:

```bash
python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_missing.json
python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_protected.json
```

Expected and observed: the first command exits `1` with
`"state": "not_required"`; the second exits `0` with `"state": "required"`
and `"admin_enforced": true`. These are GitHub-shaped fixtures, not claims
about an actual repository's current settings.

## Implementation and configuration

The CLI asks GitHub's branch-protection REST endpoint for one `OWNER/REPO` and
branch through the installed GitHub CLI. It accepts `checks[].context` and the
legacy `contexts[]` list, compares the exact name, and prints a bounded JSON
report. `--snapshot FILE` replaces the network lookup for repeatable review and
tests. No repository files or GitHub settings are changed.

The report includes `admin_enforced` because required checks may still be
bypassable by administrators. Configure the check in the repository's branch
protection settings; this tool intentionally never writes those settings.

## Safety, privacy, and limits

- The process calls `gh api` without a shell. Authentication stays with `gh`;
  the tool does not print tokens, request secrets, or run PR code.
- Do not publish protection snapshots from private repositories without review.
  JSON input is capped at 1 MiB and duplicate keys or malformed fields fail.
- This audits **branch protection only**. GitHub rulesets, bypass actors,
  check-app identity, whether the workflow actually ran, and whether the exact
  check name remains stable are outside its decision. A `required` result does
  not prove that every actor is prevented from bypassing a merge restriction.
- Review the actual PR check name and re-run after changing workflows or branch
  rules. Missing API access is an error, not a negative result.

MIT license. See [contribution guide](../../../CONTRIBUTING.md),
[changelog](../../../CHANGELOG.md), [research](../../../docs/research-2026-09-26.md),
[validation](../../../docs/validation-2026-09-26.md), and
[unposted launch copy](../../../PROMOTION.md).

Suggested topics: `github-actions`, `branch-protection`, `required-status-checks`,
`coding-agents`, `pull-request-security`. Search terms: verify required GitHub
check, AI agent PR merge gate, branch protection audit CLI.
