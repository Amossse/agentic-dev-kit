"""Gate a proposed branch against explicit review-size budgets."""

import argparse
import base64
import json
import sys
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.range_scope import OID, commit
from agentic_devkit.staged_scope import InputError, git_output, repository

MAX_RECORDS = 10_000
MAX_LIMIT = 1_000_000_000


def limit(name: str, value: int) -> int:
    if not 0 <= value <= MAX_LIMIT:
        raise InputError(f"{name} must be between 0 and {MAX_LIMIT}")
    return value


def numstat_records(raw: bytes) -> list[dict]:
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise InputError("Git returned incomplete NUL-framed numstat output")
    rows = raw[:-1].split(b"\0")
    if len(rows) > MAX_RECORDS:
        raise InputError("Git numstat output exceeds 10000 records")
    changes = []
    seen = set()
    for row in rows:
        parts = row.split(b"\t", 2)
        if len(parts) != 3:
            raise InputError("Git returned malformed numstat output")
        added_raw, deleted_raw, path = parts
        if (
            not path
            or path.startswith(b"/")
            or any(part in (b"", b".", b"..") for part in path.split(b"/"))
            or path in seen
        ):
            raise InputError("Git returned an invalid or duplicate path")
        seen.add(path)
        binary = added_raw == deleted_raw == b"-"
        if binary:
            added = deleted = changed_lines = None
        else:
            if not added_raw.isdigit() or not deleted_raw.isdigit():
                raise InputError("Git returned invalid line counts")
            added, deleted = int(added_raw), int(deleted_raw)
            changed_lines = added + deleted
        changes.append(
            {
                "path": path.decode("utf-8", "backslashreplace"),
                "path_bytes_b64": base64.b64encode(path).decode("ascii"),
                "additions": added,
                "deletions": deleted,
                "binary": binary,
                "changed_lines": changed_lines,
            }
        )
    return sorted(changes, key=lambda item: item["path_bytes_b64"])


def report(
    raw: bytes,
    max_files: int,
    max_lines: int,
    max_file_lines: int | None,
    allow_binary: bool,
    metadata: dict[str, str],
) -> tuple[dict, int]:
    changes = numstat_records(raw)
    files = len(changes)
    lines = sum(item["changed_lines"] or 0 for item in changes)
    binaries = sum(item["binary"] for item in changes)
    reasons = []
    if files > max_files:
        reasons.append("file_limit")
    if lines > max_lines:
        reasons.append("line_limit")
    if binaries and not allow_binary:
        reasons.append("binary_files")
    if max_file_lines is not None and any(
        item["changed_lines"] is not None and item["changed_lines"] > max_file_lines
        for item in changes
    ):
        reasons.append("per_file_line_limit")
    state = "empty" if not changes else "rejected" if reasons else "approved"
    result = {
        "schema_version": 1,
        "state": state,
        "budget": {
            "max_files": max_files,
            "max_lines": max_lines,
            "max_file_lines": max_file_lines,
            "allow_binary": allow_binary,
        },
        "observed": {
            "files": files,
            "changed_lines": lines,
            "binary_files": binaries,
        },
        "rejected_reasons": reasons,
        "changes": changes,
        **metadata,
    }
    return result, 3 if not changes else 1 if reasons else 0


def inspect(
    root: Path,
    base: str,
    head: str,
    max_files: int,
    max_lines: int,
    max_file_lines: int | None,
    allow_binary: bool,
) -> tuple[dict, int]:
    git, repo = repository(root)
    base_oid = commit(git, repo, base)
    head_oid = commit(git, repo, head)
    merge_base = git_output(git, repo, ["merge-base", base_oid, head_oid])
    if not OID.fullmatch(merge_base):
        raise InputError("Git returned an invalid merge-base identifier")
    merge_base_oid = merge_base[:-1].decode("ascii")
    raw = git_output(
        git,
        repo,
        [
            "diff",
            "--numstat",
            "-z",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
            merge_base_oid,
            head_oid,
            "--",
        ],
    )
    return report(
        raw,
        max_files,
        max_lines,
        max_file_lines,
        allow_binary,
        {
            "base_oid": base_oid,
            "head_oid": head_oid,
            "merge_base_oid": merge_base_oid,
        },
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--base", required=True, metavar="REV")
    parser.add_argument("--head", default="HEAD", metavar="REV")
    parser.add_argument("--max-files", required=True, type=int, metavar="N")
    parser.add_argument("--max-lines", required=True, type=int, metavar="N")
    parser.add_argument("--max-file-lines", type=int, metavar="N")
    parser.add_argument("--allow-binary", action="store_true")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        max_files = limit("--max-files", args.max_files)
        max_lines = limit("--max-lines", args.max_lines)
        max_file_lines = (
            None
            if args.max_file_lines is None
            else limit("--max-file-lines", args.max_file_lines)
        )
        result, code = inspect(
            Path(args.repository),
            args.base,
            args.head,
            max_files,
            max_lines,
            max_file_lines,
            args.allow_binary,
        )
    except InputError as exc:
        print(f"diff-budget: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True, indent=2))
    print(
        f"diff-budget: {result['state']}; {result['observed']['files']} file(s), "
        f"{result['observed']['changed_lines']} changed line(s)",
        file=sys.stderr,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
