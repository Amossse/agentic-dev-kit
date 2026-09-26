"""Read GitHub branch protection and verify a named required status check."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from agentic_devkit import __version__

MAX_BYTES = 1024 * 1024
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")


class AuditError(Exception):
    pass


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise AuditError("duplicate JSON key")
        result[key] = value
    return result


def parse(raw: bytes) -> dict:
    if len(raw) > MAX_BYTES:
        raise AuditError("protection JSON exceeds 1 MiB")
    try:
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("invalid UTF-8 protection JSON") from exc
    if not isinstance(data, dict):
        raise AuditError("protection JSON must be an object")
    return data


def inspect(data: dict, check: str) -> tuple[dict, int]:
    required = data.get("required_status_checks")
    if required is None:
        checks = []
    elif isinstance(required, dict):
        raw_checks = required.get("checks", [])
        raw_contexts = required.get("contexts", [])
        if not isinstance(raw_checks, list) or not isinstance(raw_contexts, list):
            raise AuditError("malformed required status checks")
        checks = []
        for item in raw_checks:
            if not isinstance(item, dict) or not isinstance(item.get("context"), str):
                raise AuditError("malformed required check entry")
            checks.append(item["context"])
        if any(not isinstance(item, str) for item in raw_contexts):
            raise AuditError("malformed required check context")
        checks.extend(raw_contexts)
    else:
        raise AuditError("malformed required status checks")
    admins = data.get("enforce_admins")
    if admins is not None and (
        not isinstance(admins, dict) or not isinstance(admins.get("enabled"), bool)
    ):
        raise AuditError("malformed admin enforcement")
    found = check in checks
    return {
        "state": "required" if found else "not_required",
        "check": check,
        "required_checks": sorted(set(checks)),
        "admin_enforced": admins["enabled"] if admins is not None else None,
        "source": "branch_protection_only",
    }, 0 if found else 1


def fetch(repo: str, branch: str) -> bytes:
    endpoint = f"repos/{repo}/branches/{quote(branch, safe='')}/protection"
    try:
        result = subprocess.run(
            ["gh", "api", endpoint], capture_output=True, timeout=20, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError("could not query GitHub with gh api") from exc
    if result.returncode:
        raise AuditError(
            "GitHub protection lookup failed; check access and branch protection "
            "(404 can mean missing protection or insufficient permission)"
        )
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub OWNER/REPO")
    parser.add_argument("--branch", required=True)
    parser.add_argument("--check", required=True, help="exact GitHub check context")
    parser.add_argument("--snapshot", type=Path, help="offline protection JSON fixture")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if REPO.fullmatch(args.repository) is None or ".." in args.repository:
            raise AuditError("repository must be OWNER/REPO")
        if not args.branch or any(ord(c) < 32 for c in args.branch):
            raise AuditError("invalid branch name")
        if not args.check or args.check.strip() != args.check:
            raise AuditError("check must be a nonempty exact context")
        raw = (
            args.snapshot.read_bytes()
            if args.snapshot
            else fetch(args.repository, args.branch)
        )
        report, code = inspect(parse(raw), args.check)
    except (AuditError, OSError) as exc:
        print(f"required-check-audit: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
