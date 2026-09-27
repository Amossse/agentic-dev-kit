# Release Asset Audit

Compare selected local build files with the SHA-256 digests and sizes GitHub
reports for a published release. This checks the files that were uploaded,
not just a release title or a successful build command.

[中文](README.zh-CN.md) · [Toolkit](../../../README.md)

## Problem and five-minute start

A release can exist while an asset is absent, stale, or different from the file
the maintainer just built. After publishing, run:

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.9.0
release-asset-audit OWNER/REPO --tag v1.2.3 dist/package-1.2.3.whl dist/package-1.2.3.tar.gz
```

Live lookup uses an authenticated `gh api` call; `gh auth login` is needed once.
Exit `0` means every selected file matches a same-named uploaded asset's size
and SHA-256 digest, `1` means at least one is missing or different, and `2`
means invalid input, unavailable API data, or an unreadable file.

Reproduce a positive and negative case offline with Python 3.11+:

```bash
python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_matched.json LICENSE
python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_mismatch.json LICENSE
```

Observed: the first exits `0` with `"state": "matched"`; the second exits
`1` with `"state": "rejected"` and asset state `mismatch`. The snapshots are
synthetic GitHub-shaped data, not the real v0.8.0 release. For a real run in
this project, compare the v0.8.0 wheel and source archive in `dist/` against
the [public v0.8.0 release](https://github.com/Amossse/agentic-dev-kit/releases/tag/v0.8.0).

## Architecture and configuration

The CLI calls GitHub's release-by-tag REST endpoint through the installed
GitHub CLI. It validates the exact tag, non-draft status, unique uploaded asset
names, sizes, and `sha256:` digests. Local files are hashed in chunks. Only
files named on the command line are checked. `--snapshot FILE` replaces the
network response for a repeatable test; it does not authenticate a repository.

No service credentials are configured in this package. Authentication is owned
by `gh`; the required input is `OWNER/REPO`, `--tag`, and one or more local files.

## Safety, privacy, and limits

- Read-only: no GitHub writes, shell evaluation, project-code execution, or
  upload of local file contents. The API error body is not printed.
- The tool reads each explicitly named local file and prints its filename and
  SHA-256. Filenames and digests can be sensitive; review output before sharing.
  Symlink inputs are refused.
- GitHub's reported digest is compared with the local file. This is not a
  signature, SLSA/in-toto provenance, proof of how the file was built, or proof
  that CI tested those exact bytes. It does not verify unselected release assets.
- Missing digest, malformed/oversized response, duplicate names, draft release,
  or failed API access yields exit `2`; it never becomes a false match. A forged
  `--snapshot` can produce a false result, so use live mode for publication checks.

MIT license. See [contributing](../../../CONTRIBUTING.md),
[changelog](../../../CHANGELOG.md), [research](../../../docs/research-2026-09-27.md),
[validation](../../../docs/validation-2026-09-27.md), and
[unposted launch copy](../../../PROMOTION.md).

Suggested topics: `release-engineering`, `github-releases`, `artifact-integrity`,
`coding-agents`, `supply-chain-security`. Search terms: GitHub release asset
SHA-256 audit, coding-agent release verification, published wheel digest check.
