# Agentic Dev Kit

Local evidence gates for coding-agent changes. Check **what changed**, whether it
is still reviewable, and whether it is still **the state that passed tests**.

[中文](README.zh-CN.md) · [Capabilities](#capabilities) · [Contribute](CONTRIBUTING.md)

Coding agents can finish a small bug fix while also staging unrelated CI or
configuration edits. A task summary does not establish the contents of the next
commit. This toolkit provides small, reproducible checks that a developer can run
after Claude Code, Codex, or another CLI agent finishes.

## Capabilities

| Capability | Type | Input → evidence | Status |
| --- | --- | --- | --- |
| [Staged Scope](capabilities/cli/staged-scope/README.md) | Developer CLI | Git index + literal allow paths → per-path decision and exit code | Released in v0.1.0 |
| [Range Scope](capabilities/cli/range-scope/README.md) | CI / PR CLI | Base + head commits → merge-base path decision and exit code | Released in v0.2.0 |
| [Test Proof](capabilities/cli/test-proof/README.md) | Test evidence CLI | Test command + Git state → verifiable receipt and stale-state gate | Released in v0.3.0 |
| [Diff Budget](capabilities/cli/diff-budget/README.md) | Review-size CLI | Merge-base diff + numeric budgets → per-file evidence and exit code | Released in v0.4.0 |
| [Handoff Proof](capabilities/cli/handoff-proof/README.md) | Handoff evidence CLI | Task policy + three existing gates → state-bound manifest | Released in v0.5.0 |

The main repository is the installation, contribution and release entry point.
Each capability has its own documentation and reproducible example. Future
additions must fill an observed engineering need and include a runnable check;
there are no placeholder implementations.

## Install

Requires Python 3.11+ and Git on PATH. No runtime Python dependencies or API keys.

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0
staged-scope --version
range-scope --version
test-proof --version
diff-budget --version
handoff-proof --version
```

Alternative: `python3.11 -m pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.5.0`.

## Five-minute quick start

Inside a Git working tree, review its existing staged changes, stage only the
task's intended files, then check the boundary:

```bash
git status --short
git diff --cached
staged-scope . --allow src/payments/ --allow tests/test_payments.py
```

Allow arguments are literal repository-relative paths. A trailing slash allows
that directory's descendants; without it, only the exact file matches. There
are no globs. Output is JSON on stdout and a counts-only summary on stderr.

Exit `0` means a nonempty, approved index; `1` means rejected paths or unmerged
records; `2` means invalid input or Git failure; `3` means no staged changes.
Only `0` authorizes continuation of your own workflow.

Run the complete disposable example, including the unexpected CI edit:

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/staged_scope_demo.py --installed
```

It prints three checked outcomes: empty/3, rejected/1 with
`.github/workflows/ci.yml`, approved/0. The example writes and stages synthetic
files only in a temporary repository and cleans it up on exit.
See [input, actual output and implementation](capabilities/cli/staged-scope/README.md).

For a committed branch or pull request, compare its divergence point with the
candidate head:

```bash
range-scope . --base origin/main --head HEAD --allow src/payments/ --allow tests/
```

See the [Range Scope CI checkout and demo](capabilities/cli/range-scope/README.md).

Bind a real test result to the current staged/working-tree state:

```bash
test-proof run . -- python -m unittest
test-proof verify .
```

The receipt lives in Git metadata by default. Any subsequent tracked change,
commit, or untracked file makes verification fail. See the
[Test Proof before/after demo](capabilities/cli/test-proof/README.md).

Reject an agent branch that is too large to review under your repository policy:

```bash
diff-budget . --base origin/main --head HEAD --max-files 10 --max-lines 400
```

See the [Diff Budget fixture, binary policy, and CI example](capabilities/cli/diff-budget/README.md).

Create one re-runnable handoff from the branch scope, review budget and current
Test Proof receipt:

```bash
handoff-proof create . --task "Fix payment rounding" --base origin/main \
  --allow src/payments/ --allow tests/ --max-files 10 --max-lines 400
handoff-proof verify .
```

See the [Handoff Proof rejected/valid/stale example](capabilities/cli/handoff-proof/README.md).

## Boundaries

The inspected CLI uses fixed read-only Git commands. It does not run a model,
repository hooks, external diff drivers or text conversion commands. It emits
filenames and scope rules, which may be confidential. Review output before
sharing. Use your trusted Git installation and working tree; this is not a
sandbox for malicious Git repositories.

The gates cover HEAD versus index or merge-base versus a committed head,
including both sides of a rename. They do not determine who
created an edit, verify code correctness, or lock the index until commit. Review
pre-existing staged changes and rerun after staging changes. A plain CI checkout
has an empty index; the gate requires a job that has deliberately prepared one.

Test Proof executes only the explicit argument array after `--`, but that command
inherits the user's environment and is not sandboxed. Its receipt proves an exit
code and represented Git-state match, not test quality or deterministic external
services. Command arguments are recorded; never place secrets in them.

Diff Budget treats size as a policy signal, not a quality score. Renames count
both endpoints, binaries are rejected unless explicitly allowed, and configured
exceptions remain a human/repository-policy decision.

Handoff Proof records and re-runs these local policies but does not sign them,
approve their strictness, validate the human task statement, or replace SLSA,
in-toto, GitHub artifact attestations, or repository-owner review.

## Project and contribution

MIT. [License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
· [Latest research and existing tools](docs/research-2026-09-23.md)
· [Latest validation](docs/validation-2026-09-23.md) · [Prepared launch copy](PROMOTION.md).

Search terms: Claude Code workflow, coding agent handoff, staged Git scope,
agentic developer toolkit, commit boundary, monorepo change gate, test evidence
receipt, stale test result, pull request size gate, changed lines budget, coding
agent handoff manifest, state-bound agent evidence.

Related earlier tools remain independently maintained:
[Agent Footprint](https://github.com/Amossse/agent-footprint) for filesystem
changes, [Agents Scope](https://github.com/Amossse/agents-scope) for Codex
instruction discovery, and [Plugin Preflight](https://github.com/Amossse/plugin-preflight)
for portable plugin packaging. Their code is not bundled here.
