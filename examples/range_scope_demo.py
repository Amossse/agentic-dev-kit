"""Reproduce empty, rejected and approved branch-range checks."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    command = (
        ["range-scope"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.range_scope"]
    )
    with tempfile.TemporaryDirectory(prefix="range-scope-demo-") as directory:
        root = Path(directory)

        def git(*items):
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *items],
                check=True,
                capture_output=True,
                timeout=10,
            )

        def check(base, head, expected):
            result = subprocess.run(
                [
                    *command,
                    str(root),
                    "--base",
                    base,
                    "--head",
                    head,
                    "--allow",
                    "src/",
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != expected:
                raise RuntimeError(
                    f"expected {expected}, got {result.returncode}: {result.stderr}"
                )
            report = json.loads(result.stdout)
            print(
                json.dumps(
                    {
                        "exit": result.returncode,
                        "state": report["state"],
                        "changed_records": report["changed_records"],
                        "rejected_paths": [
                            item["path"]
                            for item in report["changes"]
                            if item["rejected_reason"]
                        ],
                    },
                    sort_keys=True,
                )
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (root / "src").mkdir()
        (root / "src/payment.py").write_text("value = 1\n")
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "baseline")
        check("main", "main", 3)
        git("switch", "-qc", "topic")
        (root / "src/payment.py").write_text("value = 2\n")
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "payment fix")
        git("branch", "topic-ok")
        (root / ".github/workflows").mkdir(parents=True)
        (root / ".github/workflows/ci.yml").write_text("name: unexpected\n")
        git("add", "--", ".github/workflows/ci.yml")
        git("commit", "-qm", "unexpected CI edit")
        check("main", "topic", 1)
        check("main", "topic-ok", 0)


if __name__ == "__main__":
    main()
