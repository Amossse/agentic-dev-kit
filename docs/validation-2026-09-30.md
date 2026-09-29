# Artifact Run Audit validation, 2026-09-30

The offline example uses `examples/artifact_run_matched.json` and
`examples/workflow_run_success.json`. The artifact JSON is synthetic; no such
artifact belonged to the older v0.9.0 run.

| Check | Command/input | Actual result |
| --- | --- | --- |
| Unit tests | `python3.11 -m unittest discover -s tests -q` | 22 passed |
| Lint/format/types | `uvx ruff check . && uvx ruff format --check . && uvx ty check .` | Passed; 79 files formatted |
| Offline match | Module command in capability README with both snapshots | Exit 0, `matched` |
| Offline negative | Wrong run association, expired artifact, missing digest | Exit 1 for mismatches; exit 2 for malformed digest |
| Live GitHub match | `python3.11 -m agentic_devkit.artifact_run_audit Amossse/agentic-dev-kit --artifact 11068534090 --run 36646616190 --sha 5a10ec0eb46ba349ffa75c7d10c18ff86aa242d8 --workflow .github/workflows/ci.yml --event push` | Exit 0, `matched`; [run](https://github.com/Amossse/agentic-dev-kit/actions/runs/36646616190) succeeded on Python 3.11/3.13 |
| Live stale-SHA negative | Same command with `--sha c69386ae0df51a1bb982ddcab862f8815783f120` | Exit 1, `rejected` |
| Build/install | `uv build -q && uvx twine check dist/agentic_dev_kit-0.11.0* && uvx --from dist/agentic_dev_kit-0.11.0-py3-none-any.whl artifact-run-audit --version` | Wheel and sdist passed; CLI printed `0.11.0` |
| Security scan | `uvx bandit -q -r agentic_devkit` | Exit 1: 16 low subprocess findings, 0 medium/high; three low findings in the new fixed-argument `gh api` call. No suppressions. |
| Chinese copy scan | `rg -n -P` with `haohao-shuohua` quick-scan patterns on changed Chinese docs, README and promotion copy | 0 matches; no edits needed |

The expected positive result is exit `0` and `"state": "matched"`; stale,
expired, or failed associations return exit `1`; malformed or unavailable data
returns exit `2`. No result here claims downloaded-byte integrity.

The live artifact ID was returned by GitHub's run-artifact API. It reported
`name=agentic-dev-kit-dist`, `expired=false`, run ID `36646616190`, head SHA
`5a10ec0eb46ba349ffa75c7d10c18ff86aa242d8`, and archive digest
`sha256:ec9778d8f54341a457035a6aaee51057bc581b60604a0902842f59b09118e4fe`.
The archive was not downloaded or hashed locally. GitHub can remove it after
retention expires, so this live example is time-limited.

The new subprocess call runs trusted `gh` from PATH without a shell. Repository
and IDs are validated; API errors omit response bodies. CI upload uses the
official action pinned to commit `b7c566a772e6b6bfb58ed0dc250532a479d7789f`
(v6 at implementation time), read-only repository token permissions, and only
the distribution files built by the Python 3.11 matrix job.
