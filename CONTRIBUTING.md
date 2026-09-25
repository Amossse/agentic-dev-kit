# Contributing

Start with a public issue describing an engineering task, a concrete input,
expected evidence, existing tools and why the gap belongs in this toolkit.
Do not attach private code, real credentials or sensitive filenames.

For Staged Scope, include a disposable Git reproduction and the exact allow rules.
Changes to matching, Git arguments, framing or exit precedence need a regression
case in the existing acceptance check. Keep stdlib runtime dependencies and
literal path semantics unless a measured need justifies a change.

For Test Proof, include the command, expected Git state transition and a synthetic
repository. Changes to fingerprinting, receipt validation, execution or exit
precedence need an acceptance case. Never place credentials in command arguments.

For Diff Budget, include the base/head topology, exact numeric budget and expected
numstat. Changes to binary, rename, merge-base, count, or exit semantics need a
synthetic history case; do not present line count as a quality metric.

For Handoff Proof, include the task policy, component-gate outcomes, current Git
state and expected handoff result. Changes to manifest validation, write location,
composition, or stale-state semantics need a synthetic end-to-end case. Do not
present unsigned local JSON as authenticated provenance.

For Policy Gate, include a base commit containing the policy, a candidate branch,
and expected path/size results. Changes to base-policy trust, schema parsing, or
policy-edit handling need a synthetic history case. Do not claim the CLI itself
authenticates repository owners.

For PR Event Gate, include a synthetic `pull_request` event, base/head commits,
the checked-out HEAD, and the expected exit code. Changes to event parsing,
workflow permissions, or checkout semantics require a regression case. Never
use `pull_request_target` with untrusted checkout and secrets in this recipe.

From a clone with Python 3.11+ and Git:

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
python3.11 examples/range_scope_demo.py
python3.11 examples/test_proof_demo.py
python3.11 examples/diff_budget_demo.py
python3.11 examples/handoff_proof_demo.py
python3.11 examples/policy_gate_demo.py
python3.11 examples/pr_event_gate_demo.py
uvx ruff check .
uvx ruff format --check .
uvx ty check .
uv build
uvx twine check dist/*
```

Tests and the demo write synthetic files only in temporary repositories. Never
run a submitted reproduction in a private checkout before reviewing it.

Add a capability only after a real need is clear. Place documentation under
`capabilities/<type>/<name>/`, keep code in the installable package, add a
reproducible example and update the main matrix, bilingual docs and CHANGELOG.
One narrow runnable capability is preferable to placeholder agents or wrappers.

Submit a PR explaining the problem, resulting behavior and validation. By
contributing you agree your contribution is licensed under this project's MIT
license. For security concerns, avoid publishing working credentials or private
repositories; use GitHub private vulnerability reporting when available.
