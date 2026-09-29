# Artifact Run Audit

Check whether one GitHub Actions artifact belongs to a specified successful
workflow run and commit. A green run and a similarly named artifact are not
enough to establish that association.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Five-minute quick start

Requires Python 3.11+ and authenticated GitHub CLI (`gh auth login`). The
package has no runtime Python dependencies:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.11.0
gh api repos/OWNER/REPO/actions/runs/RUN_ID/artifacts --jq '.artifacts[] | {id,name}'
artifact-run-audit OWNER/REPO --artifact ARTIFACT_ID --run RUN_ID \
  --sha FULL_COMMIT_SHA --workflow .github/workflows/ci.yml --event push
```

Exit `0` means both GitHub records agree on the run and commit, the run
completed successfully, and the artifact is not expired. Exit `1` means a
mismatch, unsuccessful run, or expired artifact. Exit `2` means malformed data,
invalid input, or failed API access. The JSON result includes the artifact's
GitHub-reported SHA-256 archive digest; this command does not download or hash
the archive.

## Reproducible offline example

From the cloned repository root:

```bash
python3.11 -m agentic_devkit.artifact_run_audit Amossse/agentic-dev-kit \
  --artifact 12345 --run 36281705940 \
  --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 \
  --workflow .github/workflows/ci.yml --event push \
  --artifact-snapshot examples/artifact_run_matched.json \
  --run-snapshot examples/workflow_run_success.json
```

Expected and observed: exit `0`, `"state": "matched"`. Changing the artifact
association to another run ID returns exit `1`, `"state": "rejected"`. The
artifact snapshot is synthetic; it was not uploaded by run 36281705940.
The two snapshot options must be used together. See
[validation](../../../docs/validation-2026-09-30.md) for the live probe.

The live probe used artifact `11068534090`, run `36646616190`, and commit
`5a10ec0eb46ba349ffa75c7d10c18ff86aa242d8`; it returned `matched`.
This example remains queryable only while GitHub retains that artifact.

## Implementation and configuration

The CLI uses fixed, read-only `gh api` calls for one artifact ID and one run
ID. It validates bounded JSON with duplicate-key rejection. It reuses Workflow
Run Audit's exact SHA, workflow path, event, and success decision, then checks
the artifact's `workflow_run.id`, `workflow_run.head_sha`, expiry flag, and
SHA-256 digest syntax. Inputs are positional `OWNER/REPO` plus the explicit
options above. Offline snapshots substitute for both API responses.

## Security, privacy, and limits

- No code execution, archive download, token storage, or GitHub mutation. API
  errors do not print response bodies. Use a trusted `gh` binary and account.
- The digest describes the Actions artifact archive, not the individual files
  inside it. This command reads metadata only; it does not independently
  verify bytes, prove that the uploaded files were tested, or compare an
  artifact to GitHub Release assets.
- A successful run does not prove every relevant job ran or that its check is
  required. Offline snapshots can be forged. GitHub may expire or remove old
  artifacts according to retention settings.
- JSON output includes names, commit IDs, digest, and run URL; review before
  sharing private-repository results.

MIT [license](../../../LICENSE). Contributions and sanitized edge cases are
welcome via [CONTRIBUTING](../../../CONTRIBUTING.md); see the
[changelog](../../../CHANGELOG.md). Suggested topics: `github-actions`,
`artifact-integrity`, `ci-evidence`, `coding-agents`. Search terms: GitHub
Actions artifact run association, CI artifact commit SHA audit, coding agent
release evidence. [Bilingual launch copy](../../../PROMOTION.md) is prepared
but not posted.
