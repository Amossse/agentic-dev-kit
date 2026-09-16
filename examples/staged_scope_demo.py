"""Reproduce empty, rejected and approved handoffs in a disposable Git repo."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--installed", action="store_true", help="use installed staged-scope"
    )
    args = parser.parse_args()
    command = (
        ["staged-scope"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.staged_scope"]
    )
    with tempfile.TemporaryDirectory(prefix="agentic-dev-kit-demo-") as directory:
        root = Path(directory)

        def git(*items):
            subprocess.run(
                ["git", "-C", str(root), *items],
                check=True,
                capture_output=True,
                timeout=10,
            )

        def check(scopes, expected):
            result = subprocess.run(
                [
                    *command,
                    str(root),
                    *[item for scope in scopes for item in ("--allow", scope)],
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != expected:
                raise RuntimeError(
                    f"expected exit {expected}, got {result.returncode}: "
                    f"{result.stderr}"
                )
            report = json.loads(result.stdout)
            summary = {
                "exit": result.returncode,
                "state": report["state"],
                "changed_records": report["changed_records"],
                "rejected_paths": [
                    x["path"] for x in report["changes"] if x["rejected_reason"]
                ],
            }
            print(json.dumps(summary, sort_keys=True))

        git("init", "-q")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (root / "src").mkdir()
        (root / "src/payment.py").write_text(
            "def total(prices):\n    return sum(prices)\n"
        )
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "example baseline")
        check(["src/"], 3)
        (root / "src/payment.py").write_text(
            "def total(prices):\n    return round(sum(prices), 2)\n"
        )
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/ci.yml").write_text("name: unexpected CI edit\n")
        git("add", "--", "src/payment.py", ".github/workflows/ci.yml")
        check(["src/"], 1)
        # Only the synthetic CI file is unstaged; the inspected CLI never changes it.
        git("restore", "--staged", "--", ".github/workflows/ci.yml")
        check(["src/"], 0)
        if (
            root / ".github/workflows/ci.yml"
        ).read_text() != "name: unexpected CI edit\n":
            raise RuntimeError("demo unexpectedly changed the work tree")


if __name__ == "__main__":
    main()
