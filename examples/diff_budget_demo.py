"""Reproduce empty, oversized and approved branch-budget checks."""

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
        ["diff-budget"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.diff_budget"]
    )
    with tempfile.TemporaryDirectory(prefix="diff-budget-demo-") as directory:
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
                    "--max-files",
                    "1",
                    "--max-lines",
                    "4",
                ],
                cwd=Path(__file__).resolve().parents[1],
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
                        "files": report["observed"]["files"],
                        "changed_lines": report["observed"]["changed_lines"],
                        "rejected_reasons": report["rejected_reasons"],
                    },
                    sort_keys=True,
                )
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (root / "payment.py").write_text("fee = 1\ntotal = 100\n")
        git("add", "--", "payment.py")
        git("commit", "-qm", "baseline")
        check("main", "main", 3)
        git("switch", "-qc", "topic")
        (root / "payment.py").write_text("fee = 1\ntotal = 99\n")
        git("add", "--", "payment.py")
        git("commit", "-qm", "payment fix")
        git("branch", "topic-small")
        (root / "generated.py").write_text(
            "\n".join(f"item_{n} = {n}" for n in range(6)) + "\n"
        )
        git("add", "--", "generated.py")
        git("commit", "-qm", "unexpected generated file")
        check("main", "topic", 1)
        check("main", "topic-small", 0)


if __name__ == "__main__":
    main()
