"""Create and verify a state-bound coding-agent handoff manifest."""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.diff_budget import inspect as inspect_budget
from agentic_devkit.diff_budget import limit
from agentic_devkit.range_scope import inspect as inspect_range
from agentic_devkit.staged_scope import InputError, allow_paths, git_output, repository
from agentic_devkit.test_proof import verify as verify_test

MAX_MANIFEST = 2 * 1024 * 1024


def task_text(value: str) -> str:
    if (
        not value.strip()
        or len(value) > 500
        or any(ord(character) < 32 and character not in "\t\n" for character in value)
    ):
        raise InputError("task must be 1 to 500 characters without control bytes")
    return value


def manifest_path(git: str, repo: Path, value: str | None) -> Path:
    git_dir_raw = git_output(git, repo, ["rev-parse", "--absolute-git-dir"])
    if not git_dir_raw.endswith(b"\n") or not git_dir_raw[:-1]:
        raise InputError("Git returned an invalid metadata directory")
    git_dir = Path(os.fsdecode(git_dir_raw[:-1])).resolve()
    path = (
        Path(value).resolve()
        if value
        else git_dir / "agentic-dev-kit" / "handoff-proof.json"
    )
    if path.is_relative_to(repo.resolve()) and not path.is_relative_to(git_dir):
        raise InputError(
            "manifest must be outside the working tree or inside Git metadata"
        )
    return path


def write_manifest(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False
        ) as handle:
            json.dump(data, handle, ensure_ascii=True, sort_keys=True, indent=2)
            handle.write("\n")
            temporary = Path(handle.name)
        os.replace(temporary, path)
    except OSError as exc:
        raise InputError("could not write the handoff manifest") from exc


def collect(root: Path, policy: dict) -> tuple[dict, dict[str, int]]:
    scopes = allow_paths(policy["allow"])
    range_report, range_code = inspect_range(
        root, policy["base"], policy["head"], scopes
    )
    budget_report, budget_code = inspect_budget(
        root,
        policy["base"],
        policy["head"],
        policy["max_files"],
        policy["max_lines"],
        policy["max_file_lines"],
        policy["allow_binary"],
    )
    test_report, test_code = verify_test(root, policy["test_receipt"])
    return (
        {
            "range_scope": range_report,
            "diff_budget": budget_report,
            "test_proof": test_report,
        },
        {
            "range_scope": range_code,
            "diff_budget": budget_code,
            "test_proof": test_code,
        },
    )


def create(
    root: Path,
    task: str,
    policy: dict,
    output: str | None,
) -> tuple[dict, int]:
    git, repo = repository(root)
    path = manifest_path(git, repo, output)
    task = task_text(task)
    evidence, codes = collect(repo, policy)
    approved = all(code == 0 for code in codes.values())
    manifest = {
        "schema_version": 1,
        "state": "approved" if approved else "rejected",
        "task": task,
        "policy": policy,
        "evidence": evidence,
    }
    if approved:
        write_manifest(path, manifest)
    return manifest, 0 if approved else 1


def load_manifest(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError("could not read the handoff manifest") from exc
    if len(raw) > MAX_MANIFEST:
        raise InputError("handoff manifest exceeds 2 MiB")
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("handoff manifest is not valid UTF-8 JSON") from exc
    if (
        not isinstance(data, dict)
        or data.get("schema_version") != 1
        or data.get("state") != "approved"
        or not isinstance(data.get("evidence"), dict)
        or not isinstance(data.get("policy"), dict)
        or not isinstance(data.get("task"), str)
    ):
        raise InputError("unsupported or invalid handoff manifest")
    evidence_names = {"range_scope", "diff_budget", "test_proof"}
    if not evidence_names.issubset(data["evidence"]) or any(
        not isinstance(data["evidence"][name], dict) for name in evidence_names
    ):
        raise InputError("handoff manifest has invalid evidence")
    task_text(data["task"])
    policy = data["policy"]
    required_policy = {
        "base",
        "head",
        "allow",
        "max_files",
        "max_lines",
        "max_file_lines",
        "allow_binary",
        "test_receipt",
    }
    if not required_policy.issubset(policy):
        raise InputError("handoff manifest has an invalid policy")
    expected_types = {
        "base": str,
        "head": str,
        "allow": list,
        "max_files": int,
        "max_lines": int,
        "allow_binary": bool,
    }
    if any(type(policy.get(key)) is not kind for key, kind in expected_types.items()):
        raise InputError("handoff manifest has an invalid policy")
    if not all(isinstance(item, str) for item in policy["allow"]):
        raise InputError("handoff manifest has invalid allow paths")
    if (
        policy.get("max_file_lines") is not None
        and type(policy["max_file_lines"]) is not int
    ):
        raise InputError("handoff manifest has an invalid per-file budget")
    if policy.get("test_receipt") is not None and not isinstance(
        policy["test_receipt"], str
    ):
        raise InputError("handoff manifest has an invalid test receipt path")
    limit("max_files", policy["max_files"])
    limit("max_lines", policy["max_lines"])
    if policy["max_file_lines"] is not None:
        limit("max_file_lines", policy["max_file_lines"])
    return data


def verify(root: Path, source: str | None) -> tuple[dict, int]:
    git, repo = repository(root)
    path = manifest_path(git, repo, source)
    manifest = load_manifest(path)
    current, codes = collect(repo, manifest["policy"])
    matches = {
        name: codes[name] == 0 and current[name] == manifest["evidence"].get(name)
        for name in codes
    }
    valid = all(matches.values())
    return {
        "schema_version": 1,
        "state": "valid" if valid else "stale",
        "task": manifest["task"],
        "evidence_matches": matches,
    }, 0 if valid else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    create_parser = subparsers.add_parser("create", help="create an approved manifest")
    create_parser.add_argument("repository", nargs="?", default=".")
    create_parser.add_argument("--task", required=True)
    create_parser.add_argument("--base", required=True, metavar="REV")
    create_parser.add_argument("--head", default="HEAD", metavar="REV")
    create_parser.add_argument(
        "--allow", action="append", required=True, metavar="PATH"
    )
    create_parser.add_argument("--max-files", required=True, type=int, metavar="N")
    create_parser.add_argument("--max-lines", required=True, type=int, metavar="N")
    create_parser.add_argument("--max-file-lines", type=int, metavar="N")
    create_parser.add_argument("--allow-binary", action="store_true")
    create_parser.add_argument("--test-receipt", metavar="PATH")
    create_parser.add_argument("--output", metavar="PATH")
    verify_parser = subparsers.add_parser("verify", help="re-run an approved manifest")
    verify_parser.add_argument("repository", nargs="?", default=".")
    verify_parser.add_argument("--manifest", metavar="PATH")
    args = parser.parse_args(argv)
    try:
        if args.action == "create":
            max_files = limit("--max-files", args.max_files)
            max_lines = limit("--max-lines", args.max_lines)
            max_file_lines = (
                None
                if args.max_file_lines is None
                else limit("--max-file-lines", args.max_file_lines)
            )
            policy = {
                "base": args.base,
                "head": args.head,
                "allow": args.allow,
                "max_files": max_files,
                "max_lines": max_lines,
                "max_file_lines": max_file_lines,
                "allow_binary": args.allow_binary,
                "test_receipt": args.test_receipt,
            }
            report, code = create(Path(args.repository), args.task, policy, args.output)
        else:
            report, code = verify(Path(args.repository), args.manifest)
    except InputError as exc:
        print(f"handoff-proof: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(f"handoff-proof: {report['state']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
