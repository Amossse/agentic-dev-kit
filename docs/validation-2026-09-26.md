# Validation — Required Check Audit v0.8.0

All commands ran in this repository on September 26, 2026. The protected and
missing snapshots are synthetic GitHub-shaped examples; no remote settings
were changed.

| Check | Command | Result |
| --- | --- | --- |
| Full regression | `python3.11 -m unittest discover -s tests -v` | 16 tests passed |
| Lint | `uvx ruff check .` | Passed |
| Format | `uvx ruff format --check .` | 61 files already formatted |
| Type check | `uvx ty check agentic_devkit tests` | Passed |
| Security scan | `uvx bandit -q -r agentic_devkit` | 0 medium/high; 7 low subprocess findings, including existing fixed-array Git/test commands and the new fixed-array `gh api` call |
| Package | `uv build` | sdist and universal wheel built |
| Metadata | `uvx twine check dist/agentic_dev_kit-0.8.0*` | Both artifacts passed |
| Isolated install | `uvx --from dist/agentic_dev_kit-0.8.0-py3-none-any.whl required-check-audit --version` | `0.8.0` |
| Chinese copy scan | `rg -n` with the skill's section-title, contrast, meta-language and half-width-punctuation patterns across changed Chinese docs | 0 matches; no exceptions |

Reproducible behavior:

```text
python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_missing.json
exit 1; state not_required; required_checks [build]; admin_enforced false

python3.11 -m agentic_devkit.required_check_audit owner/repo --branch main --check policy --snapshot examples/required_check_protected.json
exit 0; state required; required_checks [policy]; admin_enforced true
```

Live probe:

```text
python3.11 -m agentic_devkit.required_check_audit Amossse/agentic-dev-kit --branch main --check policy
exit 2; protection lookup failed

gh api repos/Amossse/agentic-dev-kit/branches/main/protection --jq '.required_status_checks'
exit 1; gh: Branch not protected (HTTP 404)
```

The main branch was not protected at probe time, consistent with the previous
temporary test protection having been removed. The CLI deliberately maps any
failed lookup to error because a generic 404 can also hide permissions. This
live result is a current configuration observation, not evidence that the
offline protected case applies to the repository. Rulesets and bypass actors
were not audited.
