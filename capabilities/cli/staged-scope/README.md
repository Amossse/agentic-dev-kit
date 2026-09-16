# Staged Scope

Check the paths in a coding agent's proposed Git commit against the task scope.
[中文](README.zh-CN.md) · [Toolkit home](../../../README.md)

## Problem and five-minute example

A developer asks for a rounding fix in `src/payment.py`. The proposed commit also
adds `.github/workflows/ci.yml`. Both are staged. The allowed scope is `src/`.

```bash
uv tool install git+https://github.com/Amossse/agentic-dev-kit.git@v0.1.0
staged-scope . --allow src/
```

Selected output (the complete report also contains base64 filename bytes):

```json
{
  "state": "rejected",
  "changed_records": 2,
  "rejected_records": 1,
  "changes": [
    {"path": ".github/workflows/ci.yml", "status": "A", "matched_allow": null, "rejected_reason": "outside_scope"},
    {"path": "src/payment.py", "status": "M", "matched_allow": "src/", "rejected_reason": null}
  ]
}
```

Exit `1` blocks continuation. After the developer reviews and unstages the
unexpected CI file, the same command returns `approved`, one record, exit `0`.
Unstaging does not remove the file from the working tree.

Reproduce this without touching your own index:

```bash
git clone https://github.com/Amossse/agentic-dev-kit.git
cd agentic-dev-kit
python3.11 examples/staged_scope_demo.py --installed
```

Expected and locally observed stdout:

```jsonl
{"changed_records": 0, "exit": 3, "rejected_paths": [], "state": "empty"}
{"changed_records": 2, "exit": 1, "rejected_paths": [".github/workflows/ci.yml"], "state": "rejected"}
{"changed_records": 1, "exit": 0, "rejected_paths": [], "state": "approved"}
```

The demo checks actual subprocess exits and JSON and fails explicitly on a
mismatch. [Expected results](../../../examples/staged_scope_expected.json)
are also used for the release validation.

## Configuration and exact contract

```text
staged-scope [REPOSITORY] --allow PATH [--allow PATH ...]
```

Default repository: current directory. It must be a Git working tree. Nested
invocation resolves the real repository root and inspects all index paths.
Linked Git worktrees are supported by Git's own root/index resolution.

| Rule | Meaning |
| --- | --- |
| `--allow src/payment.py` | Exact case-sensitive UTF-8 byte match |
| `--allow src/` | Any raw Git path beginning with `src/`; `src2/` is outside |
| `--allow=-option.py` | Literal dash-leading filename; use `=` |
| Multiple scopes | Any matching scope approves a path; first in byte-sorted scope order is reported |
| Renames/moves | Report deletion and addition independently; approve both ends |
| Unmerged `U` | Always rejected, even inside an allowed directory |
| Initial commit | Additions compared against Git's empty baseline |
| Empty index | Explicit exit `3`, never reported as approved |

Reject absolute paths, empty/dot/dotdot components, backslashes, colons,
`* ? [ ]`, ASCII controls/DEL and invalid Unicode in allow arguments. A trailing
slash is the only directory marker. Literal `~`, spaces and Unicode are not
expanded. Limits: 1–100 scopes, 4096 characters per scope, 10000 Git status
records, 10 MiB Git stdout per command and a 10-second timeout per command.
Output is captured before the size check; this is not a hard memory limit for
very large or malicious repositories.

The CLI validates scope arguments before reading Git. Invalid input/Git errors
produce no JSON, a short stderr error, and exit `2`. Argument-parser errors can
include the invalid CLI argument, so do not put secrets in command arguments.
Normal runs produce schema-version-1 JSON and counts-only stderr. Records and
scopes are sorted/deduplicated. An unmerged path may have multiple statuses;
counts are status records, not unique filenames. `path_bytes_b64` is authoritative
for filenames; `path` uses UTF-8 with byte escapes for invalid sequences.

## Implementation and integration

The [stdlib implementation](../../../agentic_devkit/staged_scope.py) resolves
Git on PATH and calls fixed argument arrays with `shell=False`:

```text
git rev-parse --show-toplevel
git diff --cached --name-status -z --no-renames --no-ext-diff --no-textconv --ignore-submodules=none --
```

Both commands run with `core.fsmonitor=false`, no pager, optional locks disabled,
no inherited `GIT_*` overrides, and global/system Git config disabled. Repository
config is still read. The diff's NUL records preserve unusual names; matching
uses escaped-free literal bytes and never follows a changed file's symlink.

Manual local/pre-commit workflow: review pre-existing staged changes, run the
gate, inspect the actual staged content, run the relevant tests, then commit.
Only exit `0` should continue. Do not automatically expand allowed paths to make
a failure pass. No hook is installed automatically. A CI job must deliberately
prepare its candidate index; an ordinary checkout has no HEAD-versus-index diff.

## Security, privacy and limits

- The inspected CLI is read-only and offline. It does not stage, stash, restore,
  commit, fetch, execute user code/hooks, run diff drivers, or call a model.
- Trust the Git executable on PATH and the local repository. Fixed flags reduce
  incidental command execution; they are not a sandbox or Git security audit.
- All staged paths, including pre-existing staged edits, are checked. There is
  no session attribution. Unstaged/untracked files and dirty submodule contents
  are outside this check; a changed staged submodule gitlink is a normal path.
- Paths, scope rules and base64 bytes can disclose private names. Review output
  before publishing. Redirect reports to a new file outside the inspected repo
  to avoid introducing a report into the next staged commit.
- A passing path gate does not establish safe contents, correct code or complete
  tests. Index/HEAD can change after inspection; rerun immediately before commit.
- Case-sensitive byte matching does not normalize Unicode, filesystem aliases
  or case. Non-UTF-8 names can match a UTF-8 directory prefix but not an exact
  UTF-8 filename rule. Windows cannot materialize every Git filename.
- Filenames containing reserved allow-rule characters cannot be approved by an
  exact file rule. Only an explicitly approved parent directory can cover them;
  do not automatically broaden scope. This restriction favors auditable rules.
- PR commit-range checks, semantic review, glob policies, task ownership and
  signed/locked commit receipts are not implemented.

## Contribution, license and discovery

[Contributing](../../../CONTRIBUTING.md) · [Changelog](../../../CHANGELOG.md)
· [MIT](../../../LICENSE) · [Validation](../../../docs/validation-2026-09-16.md)
· [Existing alternatives](../../../docs/research-2026-09-16.md).

Keywords: Claude Code staged files, coding agent commit scope, Git index gate,
monorepo small fix, AI code review handoff. [English/Chinese launch copy](../../../PROMOTION.md)
is prepared for manual publication.
