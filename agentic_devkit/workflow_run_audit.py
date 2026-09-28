"""Verify that one GitHub Actions run succeeded for an exact commit."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.required_check_audit import (
    MAX_BYTES,
    REPO,
    AuditError,
    unique_object,
)

SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def parse(raw: bytes) -> dict:
    if len(raw) > MAX_BYTES:
        raise AuditError("workflow run JSON exceeds 1 MiB")
    try:
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("invalid UTF-8 workflow run JSON") from exc
    if not isinstance(data, dict):
        raise AuditError("workflow run JSON must be an object")
    return data


def inspect(
    data: dict, run_id: int, sha: str, workflow: str, event: str
) -> tuple[dict, int]:
    if data.get("id") != run_id or isinstance(data.get("id"), bool):
        raise AuditError("workflow run ID does not match")
    fields = ("head_sha", "path", "event", "status", "html_url")
    if (
        "conclusion" not in data
        or any(not isinstance(data.get(field), str) for field in fields)
        or not (
            data.get("conclusion") is None or isinstance(data.get("conclusion"), str)
        )
    ):
        raise AuditError("workflow run has missing or malformed fields")
    if SHA.fullmatch(data["head_sha"]) is None or not data["path"]:
        raise AuditError("workflow run has invalid head SHA or path")
    path = data["path"]
    matched = (
        data["head_sha"] == sha
        and (path == workflow or path.startswith(workflow + "@"))
        and data["event"] == event
        and data["status"] == "completed"
        and data["conclusion"] == "success"
    )
    return {
        "state": "matched" if matched else "rejected",
        "run_id": run_id,
        "expected_sha": sha,
        "actual_sha": data["head_sha"],
        "workflow": path,
        "event": data["event"],
        "status": data["status"],
        "conclusion": data["conclusion"],
        "url": data["html_url"],
        "source": "single_workflow_run",
    }, 0 if matched else 1


def fetch(repo: str, run_id: int) -> bytes:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/actions/runs/{run_id}"],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError("could not query GitHub with gh api") from exc
    if result.returncode:
        raise AuditError("GitHub workflow run lookup failed; check access and run ID")
    return result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub OWNER/REPO")
    parser.add_argument("--run", required=True, type=int, help="GitHub Actions run ID")
    parser.add_argument("--sha", required=True, help="expected full commit SHA")
    parser.add_argument(
        "--workflow", required=True, help="exact .github/workflows file"
    )
    parser.add_argument("--event", required=True, help="expected event, e.g. push")
    parser.add_argument("--snapshot", type=Path, help="offline GitHub run JSON")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if REPO.fullmatch(args.repository) is None or ".." in args.repository:
            raise AuditError("repository must be OWNER/REPO")
        if args.run <= 0:
            raise AuditError("run ID must be positive")
        if SHA.fullmatch(args.sha) is None:
            raise AuditError("sha must be a full lowercase commit SHA")
        if not args.workflow.startswith(".github/workflows/") or any(
            c in args.workflow for c in "@\r\n"
        ):
            raise AuditError("workflow must be an exact .github/workflows path")
        if not args.event or not re.fullmatch(r"[a-z_]+", args.event):
            raise AuditError("event must be a GitHub event name")
        if args.snapshot:
            with args.snapshot.open("rb") as source:
                raw = source.read(MAX_BYTES + 1)
        else:
            raw = fetch(args.repository, args.run)
        report, code = inspect(
            parse(raw), args.run, args.sha, args.workflow, args.event
        )
    except (AuditError, OSError) as exc:
        print(f"workflow-run-audit: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
