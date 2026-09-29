"""Verify an Actions artifact belongs to a successful run at an exact SHA."""

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
from agentic_devkit.workflow_run_audit import SHA
from agentic_devkit.workflow_run_audit import fetch as fetch_run
from agentic_devkit.workflow_run_audit import inspect as inspect_run
from agentic_devkit.workflow_run_audit import parse as parse_run

DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def parse(raw: bytes) -> dict:
    if len(raw) > MAX_BYTES:
        raise AuditError("artifact JSON exceeds 1 MiB")
    try:
        data = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("invalid UTF-8 artifact JSON") from exc
    if not isinstance(data, dict):
        raise AuditError("artifact JSON must be an object")
    return data


def inspect(
    artifact: dict,
    run: dict,
    artifact_id: int,
    run_id: int,
    sha: str,
    workflow: str,
    event: str,
) -> tuple[dict, int]:
    run_report, run_code = inspect_run(run, run_id, sha, workflow, event)
    if artifact.get("id") != artifact_id or isinstance(artifact.get("id"), bool):
        raise AuditError("artifact ID does not match")
    source = artifact.get("workflow_run")
    if not isinstance(source, dict):
        raise AuditError("artifact has no workflow-run association")
    if (
        not isinstance(source.get("id"), int)
        or isinstance(source.get("id"), bool)
        or not isinstance(source.get("head_sha"), str)
        or SHA.fullmatch(source["head_sha"]) is None
        or not isinstance(artifact.get("expired"), bool)
        or not isinstance(artifact.get("digest"), str)
        or DIGEST.fullmatch(artifact["digest"]) is None
        or not isinstance(artifact.get("name"), str)
        or not artifact["name"]
    ):
        raise AuditError("artifact has malformed association or digest metadata")
    matched = (
        run_code == 0
        and source["id"] == run_id
        and source["head_sha"] == sha
        and artifact["expired"] is False
    )
    return {
        "state": "matched" if matched else "rejected",
        "artifact_id": artifact_id,
        "artifact_name": artifact["name"],
        "artifact_digest": artifact["digest"],
        "artifact_expired": artifact["expired"],
        "artifact_run_id": source["id"],
        "artifact_sha": source["head_sha"],
        "run": run_report,
        "scope": "metadata_association_only",
    }, 0 if matched else 1


def fetch_artifact(repo: str, artifact_id: int) -> bytes:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/{repo}/actions/artifacts/{artifact_id}"],
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError("could not query GitHub artifact with gh api") from exc
    if result.returncode:
        raise AuditError("GitHub artifact lookup failed; check access and artifact ID")
    return result.stdout


def read_snapshot(path: Path) -> bytes:
    with path.open("rb") as source:
        return source.read(MAX_BYTES + 1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub OWNER/REPO")
    parser.add_argument("--artifact", required=True, type=int)
    parser.add_argument("--run", required=True, type=int)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--event", required=True)
    parser.add_argument("--artifact-snapshot", type=Path)
    parser.add_argument("--run-snapshot", type=Path)
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if REPO.fullmatch(args.repository) is None or ".." in args.repository:
            raise AuditError("repository must be OWNER/REPO")
        if args.artifact <= 0 or args.run <= 0:
            raise AuditError("artifact and run IDs must be positive")
        if SHA.fullmatch(args.sha) is None:
            raise AuditError("sha must be a full lowercase commit SHA")
        if not args.workflow.startswith(".github/workflows/") or any(
            c in args.workflow for c in "@\r\n"
        ):
            raise AuditError("workflow must be an exact .github/workflows path")
        if re.fullmatch(r"[a-z_]+", args.event) is None:
            raise AuditError("event must be a GitHub event name")
        if bool(args.artifact_snapshot) != bool(args.run_snapshot):
            raise AuditError("both snapshots are required for offline mode")
        artifact_raw = (
            read_snapshot(args.artifact_snapshot)
            if args.artifact_snapshot
            else fetch_artifact(args.repository, args.artifact)
        )
        run_raw = (
            read_snapshot(args.run_snapshot)
            if args.run_snapshot
            else fetch_run(args.repository, args.run)
        )
        report, code = inspect(
            parse(artifact_raw),
            parse_run(run_raw),
            args.artifact,
            args.run,
            args.sha,
            args.workflow,
            args.event,
        )
    except (AuditError, OSError) as exc:
        print(f"artifact-run-audit: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
