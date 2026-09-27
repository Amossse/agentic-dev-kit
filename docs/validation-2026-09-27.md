# Validation — Release Asset Audit v0.9.0

Run on September 27, 2026. The live comparison reads the public v0.8.0
release; the offline match/mismatch snapshots are synthetic. No release or
repository setting was changed during validation.

| Check | Command | Result |
| --- | --- | --- |
| Regression | `python3.11 -m unittest discover -s tests -q` | 18 tests passed |
| Lint and format | `uvx ruff check .`; `uvx ruff format --check .` | Passed; 67 files formatted |
| Types | `uvx ty check .` | Passed |
| Security | `uvx bandit -q -r agentic_devkit` | 0 medium/high; 10 low subprocess findings, including 3 in the new fixed-argument `gh api` path |
| Package | `uv build -q`; `uvx twine check dist/agentic_dev_kit-0.9.0*` | Wheel and sdist passed |
| Isolated install | `uvx --from dist/agentic_dev_kit-0.9.0-py3-none-any.whl release-asset-audit --version` | `0.9.0` |
| Chinese copy scan | `rg -n` with the skill's section-title, contrast, meta-language and half-width-punctuation patterns on changed Chinese copy | 0 matches; no exceptions |

Offline before/after input and observed result:

```text
python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_matched.json LICENSE
exit 0; state matched; LICENSE matched

python3.11 -m agentic_devkit.release_asset_audit owner/repo --tag v0.8.0 --snapshot examples/release_asset_mismatch.json LICENSE
exit 1; state rejected; LICENSE mismatch
```

Live read-only end-to-end probe:

```text
python3.11 -m agentic_devkit.release_asset_audit Amossse/agentic-dev-kit --tag v0.8.0 dist/agentic_dev_kit-0.8.0-py3-none-any.whl dist/agentic_dev_kit-0.8.0.tar.gz
exit 0; both selected assets matched their public GitHub Release size and SHA-256 digest
```

The v0.8.0 wheel digest was
`b7e50ddad3ce20f060bb1d0474e89e930d5f3a038fcdf3d07f0dc96905cf8d83`;
the sdist digest was
`6e1db4951546e7990212ab11e424e6d675687c1e8187f3cbc6639147904036f5`.
This proves metadata-to-local-byte equality for these selected files only. It
does not prove the release's build provenance or CI/test identity.
