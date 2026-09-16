# Validation — v0.1.0, 2026-09-16

Local platform: macOS arm64, Python 3.11.15, trusted installed Git. Runtime
dependencies: Python stdlib and Git. Ubuntu/Python 3.11 and 3.13 are configured
in CI; see the repository Actions page for their actual run results.
Windows was not validated locally.

## Commands and results

Run from the project root unless stated otherwise:

```bash
python3.11 -m unittest discover -s tests -v
python3.11 examples/staged_scope_demo.py
uvx ruff check .
uvx ruff format --check agentic_devkit tests examples
uvx ty check .
uvx bandit -r agentic_devkit -ll
uv build
uvx twine check dist/*
```

- Two runnable acceptance methods passed, with real Git/CLI subprocesses and
  parameterized malformed input/framing cases. Fixtures are temporary only.
- Observed demo outcomes equal `examples/staged_scope_expected.json`:
  empty/exit 3; unexpected CI path/exit 1; only payment path/exit 0.
- Ruff 0.16.7 lint/format and ty 0.0.81 passed.
- Bandit reported zero medium/high findings. Two low-severity findings concern
  importing subprocess and executing Git. Reviewed: trusted executable resolved
  on PATH, fixed command/flags, no shell, timeout, environment override removal,
  external diff/textconv and fsmonitor disabled. This is not a Git sandbox.
- Wheel and source archive built; both Twine metadata checks passed.
- Release source archive owner/group metadata is canonicalized to `root`/`root`
  with numeric IDs zero before upload, avoiding workstation account disclosure.

## Acceptance evidence

| Scenario | Actual behavior |
| --- | --- |
| Unborn HEAD with staged addition | A record, exit 0 when allowed |
| Unstaged/untracked content only | Empty report, exit 3 |
| Partial staging followed by more working-tree edits | Index path checked; working content unchanged |
| Nested invocation | Whole repository index checked |
| Linked worktree, clean then staged edit | Exit 3 then exit 0 using that worktree's index |
| Exact path, case mismatch, sibling prefix | Exact matches; case/sibling mismatches reject |
| Duplicate scope rules | Same deterministic report |
| Move with configured copy/rename detection | D and A remain separate; one end allowed exits 1, both exit 0 |
| Tabs, newlines, Unicode, dash-leading names | NUL framing preserves names; JSON and base64 remain reportable |
| Non-UTF-8 filename | Direct index fixture accepted under approved directory; exact base64 preserved |
| Repository fsmonitor/external diff config and GIT_DIR/GIT_INDEX_FILE overrides | Gate uses selected normal index; marker command not run |
| Unmerged staged records | Rejected even when path is allowed, exit 1 |
| Unsupported statuses/truncated framing/path escape/limits | Explicit InputError |
| Nonrepository directory | Exit 2, no JSON or raw Git stderr |
| Read-only behavior | Index bytes compared before/after each CLI check; HEAD and working content checked |

APFS rejects physical non-UTF-8 filenames. The fixture uses `git update-index
-z --index-info` to create that path in the disposable index; no claim that
macOS can materialize it. The unmerged fixture also uses real index stages,
rather than claiming a comprehensive merge-conflict matrix.

Name/status-only Git output may not invoke textconv even without the disabling
flag. Tests exercise fsmonitor/external-diff config but do not claim exhaustive
hook/textconv execution coverage; fixed command review verifies the flags.

## Installed-package end to end

Create a fresh Python 3.11 venv, install the wheel, and run outside the source
checkout with the venv's bin directory on PATH:

```bash
uv venv --python 3.11 /tmp/agentic-dev-kit-validation-venv
uv pip install --python /tmp/agentic-dev-kit-validation-venv/bin/python dist/agentic_dev_kit-0.1.0-py3-none-any.whl
# Run from a separate directory; use the full path to the clone's example script.
PATH="/tmp/agentic-dev-kit-validation-venv/bin:$PATH" /tmp/agentic-dev-kit-validation-venv/bin/python /path/to/clone/examples/staged_scope_demo.py --installed
```

Observed version: `0.1.0`. Installed console script passed all three example
outcomes outside the checkout. PATH must expose the installed console script;
selecting a venv's Python alone does not do that. Extracted source archive
contains bilingual capability docs, examples, tests, research and this record.
Its source acceptance checks can run without the original checkout.

## Content and review boundary

Public-project scans cover internal identifiers, workstation paths, credential
patterns, metadata and archive entries. Only synthetic fixture code/data and
public documentation are included. Public Git author uses a GitHub noreply
address. No PyPI publishing or community posting is configured.

Contract and bounded code review were delegated through the local Claude Code
CLI, configured to use GPT-5.5. Review had no write access; implementation and
final validation were performed by Codex. Review results were assessed against
the documented contract, not accepted as automatic correctness proof.

Known verification limits: no real model session, PR commit-range workflow,
Windows filesystem matrix, hostile Git sandbox or exhaustive conflict variants.
The current index can change after checking; exit 0 proves only observed paths.
