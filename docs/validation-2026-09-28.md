# Workflow Run Audit validation, 2026-09-28

Source commit before this change: v0.9.0 / `034d46b`. The public GitHub Actions
run [36281705940](https://github.com/Amossse/agentic-dev-kit/actions/runs/36281705940)
has that `head_sha`, workflow `.github/workflows/ci.yml`, event `push`, status
`completed`, and conclusion `success`.

| Check | Command or input | Actual result |
| --- | --- | --- |
| Unit tests | `python3.11 -m unittest discover -s tests -q` | 20 passed |
| Lint/format/types | `uvx ruff check . && uvx ruff format --check . && uvx ty check .` | Passed; 73 files formatted |
| Build/install | `uv build -q && uvx twine check dist/agentic_dev_kit-0.10.0* && uvx --from dist/agentic_dev_kit-0.10.0-py3-none-any.whl workflow-run-audit --version` | Wheel and sdist passed; installed CLI printed `0.10.0` |
| Live positive | `python3.11 -m agentic_devkit.workflow_run_audit Amossse/agentic-dev-kit --run 36281705940 --sha 034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0 --workflow .github/workflows/ci.yml --event push` | Exit 0, `matched` |
| Live stale-SHA negative | Same command with `--sha 4d2d8967aac8b74799f9f171d54aed90ac2ec109` | Exit 1, `rejected` |
| Offline positive | Positive command with `--snapshot examples/workflow_run_success.json` | Exit 0, `matched` |
| Security scan | `uvx bandit -q -r agentic_devkit` | Exit 1: 13 low subprocess findings, 0 medium/high; three low findings in the new fixed-argument `gh api` call. No suppressions. |
| Chinese copy scan | `rg -n -P` with the haohao-shuohua quick-scan patterns on new Chinese module docs, main Chinese README, promotion copy, and research | 0 matches; no edits needed |

The live check confirms one existing public run. It does not attest to this
v0.10.0 commit until its own CI has completed. The fixture is API-shaped local
data and can be edited; it is only an offline parser/decision demonstration.
The security scan findings stem from executing trusted `gh` on PATH without a
shell. Inputs are validated, arguments are fixed, errors omit API bodies, and
the operation is read-only.
