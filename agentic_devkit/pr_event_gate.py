"""Apply the base-owned policy to the checked-out GitHub pull request head."""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from agentic_devkit import __version__
from agentic_devkit.policy_gate import inspect as inspect_policy
from agentic_devkit.range_scope import commit
from agentic_devkit.staged_scope import InputError, repository

MAX_EVENT_BYTES = 1024 * 1024
SHA = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")


def unique_event_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("event file contains duplicate JSON keys")
        result[key] = value
    return result


def event_sha(event: dict, side: str) -> str:
    try:
        value = event["pull_request"][side]["sha"]
    except (KeyError, TypeError) as exc:
        raise InputError(f"pull request event has no {side} commit SHA") from exc
    if not isinstance(value, str) or SHA.fullmatch(value) is None:
        raise InputError(f"pull request event has invalid {side} commit SHA")
    return value


def inspect(root: Path, event_file: Path, event_name: str) -> tuple[dict, int]:
    if event_name != "pull_request":
        raise InputError("GITHUB_EVENT_NAME must be pull_request")
    try:
        with event_file.open("rb") as input_file:
            raw = input_file.read(MAX_EVENT_BYTES + 1)
    except OSError as exc:
        raise InputError("could not read event file") from exc
    if len(raw) > MAX_EVENT_BYTES:
        raise InputError("event file exceeds 1 MiB")
    try:
        event = json.loads(raw, object_pairs_hook=unique_event_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InputError("event file is not valid UTF-8 JSON") from exc
    if not isinstance(event, dict):
        raise InputError("event file must contain a JSON object")
    base_sha = event_sha(event, "base")
    head_sha = event_sha(event, "head")
    git, repo = repository(root)
    if commit(git, repo, "HEAD") != head_sha:
        raise InputError("checked-out HEAD differs from pull request head SHA")
    report, code = inspect_policy(repo, base_sha, head_sha)
    if report["base_oid"] != base_sha or report["head_oid"] != head_sha:
        raise InputError("Git history changed during pull request inspection")
    return report, code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--event", default=os.environ.get("GITHUB_EVENT_PATH"))
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME", ""))
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if not args.event:
            raise InputError("GITHUB_EVENT_PATH or --event is required")
        report, code = inspect(Path(args.repository), Path(args.event), args.event_name)
    except InputError as exc:
        print(f"pr-event-gate: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(f"pr-event-gate: {report['state']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
