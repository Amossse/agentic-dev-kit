"""Acceptance checks for state-bound test receipts."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class TestProofAcceptance(unittest.TestCase):
    def test_run_verify_stale_and_changed(self):
        with tempfile.TemporaryDirectory(prefix="test-proof-test-") as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                    check=True,
                    capture_output=True,
                    timeout=10,
                ).stdout

            def cli(*args):
                return subprocess.run(
                    [sys.executable, "-m", "agentic_devkit.test_proof", *args],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (root / "app.py").write_text("value = 1\n")
            git("add", "--", "app.py")
            git("commit", "-qm", "baseline")
            (root / "app.py").write_text("value = 2\n")
            git("add", "--", "app.py")

            passed = cli("run", str(root), "--", sys.executable, "-c", "assert 2 == 2")
            self.assertEqual(passed.returncode, 0, passed.stderr)
            valid = cli("verify", str(root))
            self.assertEqual(valid.returncode, 0, valid.stderr)
            self.assertEqual(json.loads(valid.stdout)["state"], "valid")

            (root / "app.py").write_text("value = 3\n")
            stale = cli("verify", str(root))
            self.assertEqual(stale.returncode, 1)
            self.assertEqual(json.loads(stale.stdout)["state"], "stale")

            changed = cli(
                "run",
                str(root),
                "--",
                sys.executable,
                "-c",
                "from pathlib import Path; Path('app.py').write_text('value = 4\\n')",
            )
            self.assertEqual(changed.returncode, 3)

    def test_failures_and_untracked_input_are_explicit(self):
        with tempfile.TemporaryDirectory(prefix="test-proof-errors-") as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "-q", "-b", "main", str(root)],
                check=True,
                timeout=10,
            )
            subprocess.run(
                ["git", "-C", str(root), "config", "user.name", "Example"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(root),
                    "config",
                    "user.email",
                    "example@example.invalid",
                ],
                check=True,
            )
            (root / "app.py").write_text("value = 1\n")
            subprocess.run(
                ["git", "-C", str(root), "add", "app.py"], check=True, timeout=10
            )
            subprocess.run(
                ["git", "-C", str(root), "commit", "-qm", "baseline"],
                check=True,
                timeout=10,
            )

            def cli(*args):
                return subprocess.run(
                    [sys.executable, "-m", "agentic_devkit.test_proof", *args],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

            failed = cli(
                "run", str(root), "--", sys.executable, "-c", "raise SystemExit(7)"
            )
            self.assertEqual(failed.returncode, 1)
            self.assertIn("command exit 7", failed.stderr)
            self.assertEqual(cli("verify", str(root)).returncode, 1)

            (root / "new.txt").write_text("not staged\n")
            untracked = cli("run", str(root), "--", sys.executable, "-c", "pass")
            self.assertEqual(untracked.returncode, 2)
            self.assertIn("stage or remove untracked", untracked.stderr)


if __name__ == "__main__":
    unittest.main()
