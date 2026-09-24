# Validation — 2026-09-24

Target: Agentic Dev Kit 0.6.0, Policy Gate. Local validation was on macOS arm64;
the release CI covers Linux with Python 3.11 and 3.13 after publishing.

## Behavior

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/policy_gate_demo.py | diff -u examples/policy_gate_expected.json -
```

Result: 12/12 test methods passed. The new acceptance case uses real temporary
Git history. A small payment fix passes; an out-of-scope documentation edit
fails; an oversized generated file fails; changing the policy on the topic
branch fails while the limits from `main` remain in force. Missing base policy
and duplicate JSON keys return exit 2 without a traceback. The example exactly
matched this output:

```jsonl
{"exit": 0, "rejected_reasons": [], "state": "approved", "step": "small_fix"}
{"exit": 1, "rejected_reasons": ["budget_exceeded"], "state": "rejected", "step": "oversized"}
{"exit": 1, "rejected_reasons": ["policy_changed", "outside_scope", "budget_exceeded"], "state": "rejected", "step": "policy_edit"}
```

The five earlier demos also ran successfully. Their prior fixture formats are
documentation snapshots; only the new Policy Gate fixture is used for bytewise
output comparison here.

## Static, security, and packaging checks

```bash
uvx ruff check .
uvx ruff format --check .
uvx ty check .
uvx bandit -q -r agentic_devkit -ll
uv build
uvx twine check dist/agentic_dev_kit-0.6.0-py3-none-any.whl dist/agentic_dev_kit-0.6.0.tar.gz
git diff --check
```

Result: all passed. Bandit reported zero medium/high findings; the pre-existing
low findings are fixed-argument subprocess calls in shared Git/Test Proof code.
A targeted scan found no internal identifiers, TQS values, AWS-key pattern, or
GitHub-token pattern in new source, docs, fixture, or tests.

## Isolated install

Wheel and source archive were installed separately into temporary Python 3.13
environments. In both, `policy-gate --version` returned `0.6.0`, and the
installed `policy_gate_demo.py --installed` exactly matched the expected fixture.
Runtime Python dependencies remain empty; Python 3.11+ and Git are required.

## Evidence boundary

These local checks establish recorded behavior and packaging, not CI, remote
commit parity, or public release availability. Those are verified after push
and tag/release creation.
