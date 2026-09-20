"""Check a proposed branch's merge-base diff against explicit literal scopes."""

import argparse
import json
import re
import sys
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.staged_scope import (
    InputError,
    allow_paths,
    git_output,
    repository,
    scope_report,
)

OID = re.compile(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\n")


def revision(value: str) -> str:
    if (
        not value
        or len(value) > 512
        or value.startswith("-")
        or ".." in value
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise InputError("revision must be one safe Git revision without a range")
    return value


def commit(git: str, repo: Path, value: str) -> str:
    raw = git_output(
        git,
        repo,
        ["rev-parse", "--verify", "--end-of-options", f"{revision(value)}^{{commit}}"],
    )
    if not OID.fullmatch(raw):
        raise InputError("Git returned an invalid commit identifier")
    return raw[:-1].decode("ascii")


def inspect(root: Path, base: str, head: str, scopes: list[bytes]) -> tuple[dict, int]:
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
            "--name-status",
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
    return scope_report(
        raw,
        scopes,
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
    parser.add_argument("--allow", action="append", required=True, metavar="PATH")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        scopes = allow_paths(args.allow)
        report, code = inspect(Path(args.repository), args.base, args.head, scopes)
    except InputError as exc:
        print(f"range-scope: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(
        f"range-scope: {report['state']}; {report['changed_records']} record(s), "
        f"{report['rejected_records']} rejected",
        file=sys.stderr,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
