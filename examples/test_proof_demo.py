"""Reproduce a passing test receipt and its invalidation after an edit."""

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
        ["test-proof"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.test_proof"]
    )
    with tempfile.TemporaryDirectory(prefix="test-proof-demo-") as directory:
        root = Path(directory)

        def git(*items):
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *items],
                check=True,
                capture_output=True,
                timeout=10,
            )

        def call(*items):
            return subprocess.run(
                [*command, *items],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=15,
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (root / "payment.py").write_text("total = 100\n")
        git("add", "--", "payment.py")
        git("commit", "-qm", "baseline")
        (root / "payment.py").write_text("total = 99\n")
        git("add", "--", "payment.py")

        run = call("run", str(root), "--", sys.executable, "-c", "assert 99 < 100")
        print(
            json.dumps(
                {"step": "run", "exit": run.returncode, "state": "passed"},
                sort_keys=True,
            )
        )
        valid = call("verify", str(root))
        print(
            json.dumps(
                {
                    "step": "verify",
                    "exit": valid.returncode,
                    "state": json.loads(valid.stdout)["state"],
                },
                sort_keys=True,
            )
        )
        (root / "payment.py").write_text("total = 98\n")
        stale = call("verify", str(root))
        print(
            json.dumps(
                {
                    "step": "edit_then_verify",
                    "exit": stale.returncode,
                    "state": json.loads(stale.stdout)["state"],
                },
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
