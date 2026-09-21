"""Run a test command and bind its result to an unchanged Git state."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.staged_scope import InputError, git_output, repository

OID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
SHA256 = re.compile(r"[0-9a-f]{64}")
MAX_RECEIPT = 1024 * 1024


def snapshot(git: str, repo: Path) -> dict[str, object]:
    head = git_output(git, repo, ["rev-parse", "--verify", "HEAD^{commit}"])
    if not head.endswith(b"\n") or not OID.fullmatch(
        head[:-1].decode("ascii", "ignore")
    ):
        raise InputError("repository HEAD is not a valid commit")
    diff = git_output(
        git,
        repo,
        [
            "diff",
            "--binary",
            "--full-index",
            "--no-color",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
            "HEAD",
            "--",
        ],
    )
    untracked = git_output(
        git, repo, ["ls-files", "--others", "--exclude-standard", "-z", "--"]
    )
    if untracked and not untracked.endswith(b"\0"):
        raise InputError("Git returned incomplete untracked-file output")
    records = 0 if not untracked else untracked.count(b"\0")
    if records > 10_000:
        raise InputError("untracked-file count exceeds 10000")
    return {
        "head_oid": head[:-1].decode("ascii"),
        "diff_sha256": hashlib.sha256(diff).hexdigest(),
        "untracked_records": records,
    }


def receipt_path(git: str, repo: Path, value: str | None) -> Path:
    git_dir_raw = git_output(git, repo, ["rev-parse", "--absolute-git-dir"])
    if not git_dir_raw.endswith(b"\n") or not git_dir_raw[:-1]:
        raise InputError("Git returned an invalid metadata directory")
    git_dir = Path(os.fsdecode(git_dir_raw[:-1])).resolve()
    path = (
        Path(value).resolve()
        if value
        else git_dir / "agentic-dev-kit" / "test-proof.json"
    )
    repo_resolved = repo.resolve()
    if path.is_relative_to(repo_resolved) and not path.is_relative_to(git_dir):
        raise InputError(
            "receipt must be outside the working tree or inside Git metadata"
        )
    return path


def write_receipt(path: Path, data: dict[str, object]) -> None:
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
        raise InputError("could not write the test receipt") from exc


def run(root: Path, command: list[str], receipt: str | None) -> tuple[Path, dict, int]:
    if not command or not command[0]:
        raise InputError("provide a command after --")
    git, repo = repository(root)
    before = snapshot(git, repo)
    if before["untracked_records"]:
        raise InputError("stage or remove untracked files before running tests")
    started_at = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    started = time.monotonic_ns()
    try:
        completed = subprocess.run(command, cwd=repo, check=False)
    except OSError as exc:
        raise InputError("could not start the requested command") from exc
    duration_ms = (time.monotonic_ns() - started) // 1_000_000
    after = snapshot(git, repo)
    changed = before != after
    state = (
        "changed" if changed else "passed" if completed.returncode == 0 else "failed"
    )
    data = {
        "schema_version": 1,
        "state": state,
        "command": command,
        "exit_code": completed.returncode,
        "started_at": started_at,
        "duration_ms": duration_ms,
        "before": before,
        "after": after,
    }
    path = receipt_path(git, repo, receipt)
    write_receipt(path, data)
    return path, data, 3 if changed else 0 if completed.returncode == 0 else 1


def load_receipt(path: Path) -> dict:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise InputError("could not read the test receipt") from exc
    if len(raw) > MAX_RECEIPT:
        raise InputError("test receipt exceeds 1 MiB")
    try:
        data = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("test receipt is not valid UTF-8 JSON") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise InputError("unsupported test receipt schema")
    if data.get("state") not in {"passed", "failed", "changed"}:
        raise InputError("test receipt has an invalid state")
    if (
        not isinstance(data.get("command"), list)
        or not data["command"]
        or not all(isinstance(item, str) for item in data["command"])
    ):
        raise InputError("test receipt has an invalid command")
    if (
        type(data.get("exit_code")) is not int
        or type(data.get("duration_ms")) is not int
        or data["duration_ms"] < 0
        or not isinstance(data.get("started_at"), str)
    ):
        raise InputError("test receipt has invalid numeric fields")
    for key in ("before", "after"):
        value = data.get(key)
        if (
            not isinstance(value, dict)
            or not isinstance(value.get("head_oid"), str)
            or not OID.fullmatch(value["head_oid"])
            or not isinstance(value.get("diff_sha256"), str)
            or not SHA256.fullmatch(value["diff_sha256"])
            or type(value.get("untracked_records")) is not int
            or value["untracked_records"] < 0
        ):
            raise InputError("test receipt has an invalid Git snapshot")
    if (data["state"] == "changed") == (data["before"] == data["after"]):
        raise InputError("test receipt state conflicts with its Git snapshots")
    return data


def verify(root: Path, receipt: str | None) -> tuple[dict, int]:
    git, repo = repository(root)
    path = receipt_path(git, repo, receipt)
    data = load_receipt(path)
    current = snapshot(git, repo)
    matches = current == data["after"]
    valid = data["state"] == "passed" and matches
    report = {
        "schema_version": 1,
        "state": "valid" if valid else "stale" if not matches else data["state"],
        "receipt_state": data["state"],
        "head_matches": current["head_oid"] == data["after"]["head_oid"],
        "diff_matches": current["diff_sha256"] == data["after"]["diff_sha256"],
        "untracked_matches": current["untracked_records"]
        == data["after"]["untracked_records"],
    }
    return report, 0 if valid else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="action", required=True)
    run_parser = subparsers.add_parser("run", help="run a command and write a receipt")
    run_parser.add_argument("repository", nargs="?", default=".")
    run_parser.add_argument("--receipt", metavar="PATH")
    run_parser.add_argument("command", nargs=argparse.REMAINDER)
    verify_parser = subparsers.add_parser("verify", help="verify the latest receipt")
    verify_parser.add_argument("repository", nargs="?", default=".")
    verify_parser.add_argument("--receipt", metavar="PATH")
    args = parser.parse_args(argv)
    try:
        if args.action == "run":
            command = args.command[1:] if args.command[:1] == ["--"] else args.command
            _, data, code = run(Path(args.repository), command, args.receipt)
            print(
                f"test-proof: {data['state']}; command exit {data['exit_code']}; "
                "receipt written",
                file=sys.stderr,
            )
            return code
        report, code = verify(Path(args.repository), args.receipt)
    except InputError as exc:
        print(f"test-proof: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(f"test-proof: {report['state']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
