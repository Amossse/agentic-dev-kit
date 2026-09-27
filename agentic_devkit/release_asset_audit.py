"""Compare local files with published GitHub release asset digests."""

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

from agentic_devkit import __version__
from agentic_devkit.required_check_audit import (
    MAX_BYTES,
    REPO,
    AuditError,
    unique_object,
)

TAG = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+/-]*\Z")
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


def parse(raw: bytes, tag: str) -> dict[str, dict]:
    if len(raw) > MAX_BYTES:
        raise AuditError("release JSON exceeds 1 MiB")
    try:
        release = json.loads(raw, object_pairs_hook=unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AuditError("invalid UTF-8 release JSON") from exc
    if not isinstance(release, dict) or release.get("tag_name") != tag:
        raise AuditError("release tag is missing or does not match")
    if release.get("draft") is not False:
        raise AuditError("release is draft or draft state is unknown")
    assets = release.get("assets")
    if not isinstance(assets, list):
        raise AuditError("release assets must be a list")
    by_name = {}
    for asset in assets:
        if not isinstance(asset, dict):
            raise AuditError("malformed release asset")
        name, digest, size = (
            asset.get("name"),
            asset.get("digest"),
            asset.get("size"),
        )
        if (
            not isinstance(name, str)
            or not name
            or name in by_name
            or not isinstance(digest, str)
            or DIGEST.fullmatch(digest) is None
            or type(size) is not int
            or size < 0
            or asset.get("state") != "uploaded"
        ):
            raise AuditError("duplicate or malformed release asset metadata")
        by_name[name] = {"digest": digest, "size": size}
    return by_name


def fetch(repo: str, tag: str) -> bytes:
    endpoint = f"repos/{repo}/releases/tags/{quote(tag, safe='')}"
    try:
        result = subprocess.run(
            ["gh", "api", endpoint], capture_output=True, timeout=20, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AuditError("could not query GitHub with gh api") from exc
    if result.returncode:
        raise AuditError("GitHub release lookup failed; check tag and access")
    return result.stdout


def checksum(path: Path) -> tuple[str, int]:
    if path.is_symlink() or not path.is_file():
        raise AuditError("asset path must be a regular file, not a symlink")
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as input_file:
            while chunk := input_file.read(1024 * 1024):
                digest.update(chunk)
                size += len(chunk)
    except OSError as exc:
        raise AuditError("could not read local asset") from exc
    return f"sha256:{digest.hexdigest()}", size


def inspect(assets: dict[str, dict], paths: list[Path]) -> tuple[dict, int]:
    results = []
    names = set()
    for path in paths:
        name = path.name
        if name in names:
            raise AuditError("local asset filenames must be distinct")
        names.add(name)
        local_digest, local_size = checksum(path)
        published = assets.get(name)
        state = (
            "missing"
            if published is None
            else "matched"
            if local_digest == published["digest"] and local_size == published["size"]
            else "mismatch"
        )
        results.append({"name": name, "state": state, "local_sha256": local_digest})
    matched = all(r["state"] == "matched" for r in results)
    return {
        "state": "matched" if matched else "rejected",
        "assets": results,
        "scope": "selected_assets_only",
    }, 0 if matched else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", help="GitHub OWNER/REPO")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--snapshot", type=Path, help="offline GitHub release JSON")
    parser.add_argument("assets", nargs="+", type=Path, help="local files to compare")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        if REPO.fullmatch(args.repository) is None or ".." in args.repository:
            raise AuditError("repository must be OWNER/REPO")
        if TAG.fullmatch(args.tag) is None or ".." in args.tag:
            raise AuditError("invalid release tag")
        if args.snapshot:
            with args.snapshot.open("rb") as input_file:
                raw = input_file.read(MAX_BYTES + 1)
        else:
            raw = fetch(args.repository, args.tag)
        report, code = inspect(parse(raw, args.tag), args.assets)
    except (AuditError, OSError) as exc:
        print(f"release-asset-audit: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, sort_keys=True, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
