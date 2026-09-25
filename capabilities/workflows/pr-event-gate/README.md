# PR Event Gate

Bind a coding-agent PR check to GitHub's pull-request event and the exact
checked-out head, then apply the repository policy from the base commit.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Problem

`policy-gate --base origin/main --head HEAD` is useful locally, but a CI recipe
can accidentally pass a stale or contributor-chosen base ref or inspect GitHub's
synthetic merge commit. This capability validates the event's base/head commit
SHAs, requires the checked-out HEAD to equal the event head, and runs the existing
Policy Gate. It does not merely print a suggested workflow: the installed CLI
executes the check, and a reusable workflow wires it into `pull_request`.

## Five-minute start

1. Commit [Policy Gate's six-field `.agentic-dev-kit/policy.json`](../../cli/policy-gate/README.md)
   on the protected base branch.
2. Copy [`caller.yml`](caller.yml) into your repository's
   `.github/workflows/agent-pr-policy.yml`, or use its `workflow_call` job.
3. Open a PR. Make `policy` a required status check after reviewing its result.

The caller invokes this toolkit's versioned
[`pr-event-gate.yml`](../../../.github/workflows/pr-event-gate.yml), which installs
the released CLI, checks out the event head with full history and no persisted
credentials, and runs `pr-event-gate .`. Only `contents: read` is requested.
Do not use `pull_request_target`, forward secrets, or run candidate code in this
job. Version-tag and GitHub-hosted action updates should be reviewed or pinned
to commit SHAs according to your supply-chain policy.

Local installation and synthetic end-to-end demonstration:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.7.0
git clone --branch v0.7.0 --depth 1 https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/pr_event_gate_demo.py --installed
```

Expected and observed output (`examples/pr_event_gate_expected.json`):

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 2, "rejected_reasons": [], "state": "error", "step": "wrong_checkout"}
{"exit": 1, "rejected_reasons": ["outside_scope"], "state": "rejected", "step": "outside_scope"}
```

For a local fixture or CI diagnosis, provide an event file explicitly:

```bash
pr-event-gate . --event ./event.json --event-name pull_request
```

In GitHub Actions it defaults to `GITHUB_EVENT_PATH` and `GITHUB_EVENT_NAME`.
Exit codes are 0 approved nonempty diff, 1 rejected, 2 event/input/Git error,
3 empty diff. stdout is Policy Gate JSON; stderr is a short state or error.

## Architecture and configuration

The CLI accepts only the `pull_request` event, caps JSON at 1 MiB, rejects
duplicate keys, and requires lowercase 40- or 64-character hex SHA fields.
It resolves repository HEAD, demands exact equality to the event head, then
passes event base/head SHAs to Policy Gate. That tool loads and validates the
policy from the base commit and evaluates merge-base-to-head paths and size.
No new policy schema or network API is introduced. Configuration is the base
policy plus the caller's required-check and repository protection settings.

## Security, privacy, and limits

- A local `--event` file can be forged. In CI, the trust boundary is GitHub's
  `pull_request` event file, workflow definition, selected toolkit version, and
  protected base branch. This CLI cannot authenticate GitHub independently.
- The job does not run project tests or candidate code. It reads Git history;
  use isolated runners and review dependencies/actions before granting secrets.
- `pull_request_target` with untrusted checkout and secrets is deliberately
  unsupported. The job must be required for merge; this package cannot configure
  branch protection, CODEOWNERS, or policy-update exceptions.
- Missing base objects, shallow history, malformed JSON and mismatched checkout
  fail closed. Fork PRs depend on checkout being able to fetch event SHA/history.
- The JSON report contains file paths and commit IDs. Review before sharing.
  Do not put credentials or personal data in the policy or event fixtures.

Runtime dependencies: Python 3.11+ standard library and Git. The reusable
workflow needs GitHub-hosted runner access to install the tagged toolkit.
The synthetic demo does not prove a third-party repository's required-check or
fork configuration; validate those in your own repository.

## Contribution and discovery

MIT license; see [contributing](../../../CONTRIBUTING.md),
[changelog](../../../CHANGELOG.md), [research](../../../docs/research-2026-09-25.md),
[validation](../../../docs/validation-2026-09-25.md), and
[prepared, unposted launch copy](../../../PROMOTION.md). Submit synthetic event
and Git-history fixtures for changes to event trust or checkout semantics.

Suggested topics: `github-actions`, `pull-request-security`, `coding-agents`,
`agent-policy`, `code-review-automation`. Search terms: trusted PR base SHA,
coding-agent CI guardrail, GitHub pull request policy gate, agent PR scope check.
