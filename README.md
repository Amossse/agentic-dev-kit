# Agentic Dev Kit

Local evidence gates for coding-agent changes. Start with a concrete question:
**does the staged commit stay inside the task's approved files?**

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

The main repository is the installation, contribution and release entry point.
Each capability has its own documentation and reproducible example. Future
additions must fill an observed engineering need and include a runnable check;
there are no placeholder implementations.

## Install

Requires Python 3.11+ and Git on PATH. No runtime Python dependencies or API keys.

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0
staged-scope --version
range-scope --version
```

Alternative: `python3.11 -m pip install git+https://github.com/Amossse/agentic-dev-kit.git@v0.2.0`.

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

## Project and contribution

MIT. [License](LICENSE) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)
· [Latest research and existing tools](docs/research-2026-09-20.md)
· [Latest validation](docs/validation-2026-09-20.md) · [Prepared launch copy](PROMOTION.md).

Search terms: Claude Code workflow, coding agent handoff, staged Git scope,
agentic developer toolkit, commit boundary, monorepo change gate.

Related earlier tools remain independently maintained:
[Agent Footprint](https://github.com/Amossse/agent-footprint) for filesystem
changes, [Agents Scope](https://github.com/Amossse/agents-scope) for Codex
instruction discovery, and [Plugin Preflight](https://github.com/Amossse/plugin-preflight)
for portable plugin packaging. Their code is not bundled here.
