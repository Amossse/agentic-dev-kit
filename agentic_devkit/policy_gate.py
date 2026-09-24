"""Check a branch against the policy stored in its base commit."""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.diff_budget import inspect as inspect_budget
from agentic_devkit.diff_budget import limit
from agentic_devkit.range_scope import commit
from agentic_devkit.range_scope import inspect as inspect_range
from agentic_devkit.staged_scope import InputError, allow_paths, git_output, repository

POLICY_PATH = ".agentic-dev-kit/policy.json"
MAX_POLICY_BYTES = 64 * 1024


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("base policy contains duplicate JSON keys")
        result[key] = value
    return result


def load_policy(git: str, repo: Path, base_oid: str) -> tuple[dict, str]:
    raw = git_output(git, repo, ["cat-file", "blob", f"{base_oid}:{POLICY_PATH}"])
    if len(raw) > MAX_POLICY_BYTES:
        raise InputError("policy exceeds 64 KiB")
    try:
        policy = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("base policy is not valid UTF-8 JSON") from exc
    if not isinstance(policy, dict) or set(policy) != {
        "schema_version",
        "allow",
        "max_files",
        "max_lines",
        "max_file_lines",
        "allow_binary",
    }:
        raise InputError("base policy has an invalid schema")
    if type(policy["schema_version"]) is not int or policy["schema_version"] != 1:
        raise InputError("unsupported base policy schema version")
    if not isinstance(policy["allow"], list) or not all(
        isinstance(value, str) for value in policy["allow"]
    ):
        raise InputError("base policy has invalid allow paths")
    policy["allow"] = [value.decode("utf-8") for value in allow_paths(policy["allow"])]
    for key in ("max_files", "max_lines"):
        if type(policy[key]) is not int:
            raise InputError(f"base policy has invalid {key}")
        limit(key, policy[key])
    if policy["max_file_lines"] is not None:
        if type(policy["max_file_lines"]) is not int:
            raise InputError("base policy has invalid max_file_lines")
        limit("max_file_lines", policy["max_file_lines"])
    if type(policy["allow_binary"]) is not bool:
        raise InputError("base policy has invalid allow_binary")
    return policy, hashlib.sha256(raw).hexdigest()


def inspect(root: Path, base: str, head: str) -> tuple[dict, int]:
    git, repo = repository(root)
    base_oid = commit(git, repo, base)
    head_oid = commit(git, repo, head)
    policy, policy_sha256 = load_policy(git, repo, base_oid)
    scopes = allow_paths(policy["allow"])
    range_report, range_code = inspect_range(repo, base_oid, head_oid, scopes)
    budget_report, budget_code = inspect_budget(
        repo,
        base_oid,
        head_oid,
        policy["max_files"],
        policy["max_lines"],
        policy["max_file_lines"],
        policy["allow_binary"],
    )
    policy_path_b64 = base64.b64encode(POLICY_PATH.encode("ascii")).decode("ascii")
    policy_changed = any(
        change["path_bytes_b64"] == policy_path_b64
        for change in range_report["changes"]
    )
    if (
        range_report["head_oid"] != budget_report["head_oid"]
        or range_report["merge_base_oid"] != budget_report["merge_base_oid"]
    ):
        raise InputError("Git history changed during policy inspection")
    reasons = []
    if policy_changed:
        reasons.append("policy_changed")
    if range_code == 1:
        reasons.append("outside_scope")
    if budget_code == 1:
        reasons.append("budget_exceeded")
    empty = range_code == budget_code == 3
    state = "empty" if empty else "rejected" if reasons else "approved"
    report = {
        "schema_version": 1,
        "state": state,
        "policy_source": f"{base_oid}:{POLICY_PATH}",
        "policy_sha256": policy_sha256,
        "base_oid": base_oid,
        "head_oid": range_report["head_oid"],
        "merge_base_oid": range_report["merge_base_oid"],
        "rejected_reasons": reasons,
        "range_scope": range_report,
        "diff_budget": budget_report,
    }
    return report, 3 if empty else 1 if reasons else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--base", required=True, metavar="REV")
    parser.add_argument("--head", default="HEAD", metavar="REV")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        report, code = inspect(Path(args.repository), args.base, args.head)
    except InputError as exc:
        print(f"policy-gate: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(f"policy-gate: {report['state']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
