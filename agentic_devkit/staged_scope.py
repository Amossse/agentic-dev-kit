"""Check HEAD-versus-index paths against explicit literal task scopes."""

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from agentic_devkit import __version__

MAX_RECORDS = 10_000
MAX_OUTPUT = 10 * 1024 * 1024


class InputError(ValueError):
    """A public diagnostic without raw Git stderr or private input values."""


def allow_paths(values: list[str]) -> list[bytes]:
    if not 1 <= len(values) <= 100:
        raise InputError("provide between 1 and 100 --allow paths")
    result = []
    for value in values:
        parts = value.removesuffix("/").split("/")
        if (
            len(value) > 4096
            or any(part in ("", ".", "..") for part in parts)
            or re.search(r"[\\:*?\[\]\x00-\x1f\x7f]", value)
        ):
            raise InputError("--allow requires a literal relative file or directory/")
        try:
            result.append(value.encode("utf-8"))
        except UnicodeEncodeError as exc:
            raise InputError("--allow must be valid Unicode") from exc
    return sorted(set(result))


def git_output(git: str, root: Path, args: list[str]) -> bytes:
    # Do not inherit alternate indexes, work trees, injected config or diff commands.
    env = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    env.update(
        GIT_OPTIONAL_LOCKS="0", GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull
    )
    try:
        # ponytail: capture then cap output; stream if very large indexes matter.
        completed = subprocess.run(
            [git, "--no-pager", "-c", "core.fsmonitor=false", "-C", str(root), *args],
            env=env,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise InputError("Git exceeded the 10-second command timeout") from exc
    except (OSError, ValueError) as exc:
        raise InputError("could not run Git in the selected directory") from exc
    if completed.returncode:
        raise InputError("Git inspection failed; check access and index state")
    if len(completed.stdout) > MAX_OUTPUT:
        raise InputError("Git output exceeds 10 MiB")
    return completed.stdout


def records(raw: bytes) -> list[tuple[bytes, str]]:
    if not raw:
        return []
    if not raw.endswith(b"\0"):
        raise InputError("Git returned incomplete NUL-framed output")
    tokens = raw[:-1].split(b"\0")
    if len(tokens) % 2 or len(tokens) // 2 > MAX_RECORDS:
        raise InputError("Git record framing or 10000-record limit failed")
    result = []
    for status, path in zip(tokens[::2], tokens[1::2], strict=True):
        if status not in (b"A", b"M", b"D", b"T", b"U") or not path:
            raise InputError("Git returned an unsupported status or empty path")
        if path.startswith(b"/") or any(
            p in (b"", b".", b"..") for p in path.split(b"/")
        ):
            raise InputError("Git returned a non-relative path")
        result.append((path, status.decode("ascii")))
    return sorted(set(result))


def inspect(root: Path, scopes: list[bytes]) -> tuple[dict, int]:
    git = shutil.which("git")
    if git is None:
        raise InputError("Git is required on PATH")
    top = git_output(git, root, ["rev-parse", "--show-toplevel"])
    if not top.endswith(b"\n") or not top[:-1]:
        raise InputError("select a Git working tree")
    repo = Path(os.fsdecode(top[:-1]))
    raw = git_output(
        git,
        repo,
        [
            "diff",
            "--cached",
            "--name-status",
            "-z",
            "--no-renames",
            "--no-ext-diff",
            "--no-textconv",
            "--ignore-submodules=none",
            "--",
        ],
    )
    changes = []
    for path, status in records(raw):
        matched = next(
            (
                scope
                for scope in scopes
                if path == scope or (scope.endswith(b"/") and path.startswith(scope))
            ),
            None,
        )
        reason = (
            "unmerged"
            if status == "U"
            else "outside_scope"
            if matched is None
            else None
        )
        changes.append(
            {
                "path": path.decode("utf-8", "backslashreplace"),
                # Display escapes can collide; retain exact filename bytes too.
                "path_bytes_b64": base64.b64encode(path).decode("ascii"),
                "status": status,
                "matched_allow": matched.decode("utf-8") if matched else None,
                "rejected_reason": reason,
            }
        )
    rejected = sum(change["rejected_reason"] is not None for change in changes)
    state = "empty" if not changes else "rejected" if rejected else "approved"
    return {
        "schema_version": 1,
        "state": state,
        "allow": [scope.decode("utf-8") for scope in scopes],
        "changed_records": len(changes),
        "rejected_records": rejected,
        "changes": changes,
    }, 3 if not changes else 1 if rejected else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", nargs="?", default=".")
    parser.add_argument("--allow", action="append", required=True, metavar="PATH")
    parser.add_argument("--version", action="version", version=__version__)
    args = parser.parse_args(argv)
    try:
        scopes = allow_paths(args.allow)
        report, code = inspect(Path(args.repository), scopes)
    except InputError as exc:
        print(f"staged-scope: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True, indent=2))
    print(
        f"staged-scope: {report['state']}; {report['changed_records']} record(s), "
        f"{report['rejected_records']} rejected",
        file=sys.stderr,
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
