"""Reproduce rejected, approved, valid, and stale handoff outcomes."""

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
    test_command = (
        ["test-proof"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.test_proof"]
    )
    handoff_command = (
        ["handoff-proof"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.handoff_proof"]
    )
    with tempfile.TemporaryDirectory(prefix="handoff-proof-demo-") as directory:
        root = Path(directory)

        def git(*items):
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *items],
                check=True,
                capture_output=True,
                timeout=10,
            )

        def handoff(*items):
            return subprocess.run(
                [*handoff_command, *items],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=15,
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (root / "src").mkdir()
        (root / "src/payment.py").write_text("total = 100\n")
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "baseline")
        git("switch", "-qc", "topic")
        (root / "src/payment.py").write_text("total = 99\n")
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "fix payment total")
        tested = subprocess.run(
            [
                *test_command,
                "run",
                str(root),
                "--",
                sys.executable,
                "-c",
                "assert 99 < 100",
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if tested.returncode != 0:
            raise RuntimeError(tested.stderr)

        common = [
            str(root),
            "--task",
            "Fix payment rounding",
            "--base",
            "main",
            "--max-files",
            "2",
            "--max-lines",
            "10",
        ]
        rejected = handoff("create", *common, "--allow", "docs/")
        rejected_report = json.loads(rejected.stdout)
        print(
            json.dumps(
                {
                    "step": "wrong_scope",
                    "exit": rejected.returncode,
                    "state": rejected_report["state"],
                },
                sort_keys=True,
            )
        )
        created = handoff("create", *common, "--allow", "src/")
        created_report = json.loads(created.stdout)
        print(
            json.dumps(
                {
                    "step": "create",
                    "exit": created.returncode,
                    "state": created_report["state"],
                },
                sort_keys=True,
            )
        )
        valid = handoff("verify", str(root))
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
        (root / "src/payment.py").write_text("total = 98\n")
        stale = handoff("verify", str(root))
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
