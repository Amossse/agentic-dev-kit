# Workflow Run Audit

Verify that one GitHub Actions run completed successfully for an exact commit,
workflow file, and event. A green run from a different commit is not evidence for
the commit you are about to release or hand off.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Five-minute quick start

Install Python 3.11+ and the GitHub CLI, then authenticate with `gh auth login`.
The package has no runtime Python dependencies:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.10.0
workflow-run-audit OWNER/REPO --run 123456789 --sha FULL_COMMIT_SHA \
  --workflow .github/workflows/ci.yml --event push
```

Get the run ID from its Actions URL and the full commit ID from `git rev-parse
HEAD`. Exit `0` means every field matches and the run has `status=completed` and
`conclusion=success`; `1` means a mismatch, pending run, or failed run; `2`
means invalid input, unreadable API response, or failed lookup. JSON is printed
to stdout for automation.

## Reproducible example

This recorded v0.9.0 run is publicly queryable:

```bash
workflow-run-audit Amossse/agentic-dev-kit --run 36281705940 \
  --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push
```

Expected and observed: exit `0`, `"state": "matched"`. Replacing the SHA with
another full SHA returns exit `1`, `"state": "rejected"`. Without GitHub access,
use the recorded API-shaped fixture:

```bash
python3.11 -m agentic_devkit.workflow_run_audit Amossse/agentic-dev-kit \
  --run 36281705940 --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push \
  --snapshot examples/workflow_run_success.json
```

The fixture is untrusted local data; it demonstrates the decision, not a fresh
GitHub verification. See [validation](../../../docs/validation-2026-09-28.md).

## Implementation and configuration

The CLI calls `gh api repos/OWNER/REPO/actions/runs/RUN_ID` with fixed argument
boundaries and never uses a shell. It validates a bounded JSON response,
rejects duplicate keys, and compares the returned run ID, `head_sha`, workflow
`path`, `event`, `status`, and `conclusion` with explicit inputs. `--snapshot`
replaces the API response for offline tests. No configuration file or token is
stored by the toolkit; `gh` manages authentication.

## Limits, security, and privacy

- Read-only: no workflow rerun, checkout, code execution, or GitHub mutation.
- A successful run does not prove which jobs or tests ran, that the workflow
  definition was safe, that its check is required, or that an artifact matches
  the tested bytes. Use Required Check Audit and Release Asset Audit for their
  separate questions.
- The supplied run ID must come from the intended repository. Offline snapshots
  can be forged. GitHub may remove old runs according to retention settings.
- Output includes commit IDs, workflow paths, and the run URL. Review before
  sharing private-repository output. API error bodies and credentials are not
  printed. Use your trusted `gh` installation and account.

MIT [license](../../../LICENSE). Contributions and sanitized edge cases are
welcome via [CONTRIBUTING](../../../CONTRIBUTING.md); see the
[changelog](../../../CHANGELOG.md). Suggested GitHub topics:
`github-actions`, `ci-evidence`, `coding-agents`, `release-engineering`.
Search terms: exact commit CI verification, GitHub Actions run SHA audit,
agent handoff workflow evidence. [English and Chinese launch copy](../../../PROMOTION.md)
is prepared but not posted.
