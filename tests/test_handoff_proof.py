"""Acceptance checks for state-bound coding-agent handoff manifests."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class HandoffProofAcceptance(unittest.TestCase):
    def test_create_and_verify_approved_handoff(self):
        with tempfile.TemporaryDirectory(prefix="handoff-proof-test-") as directory:
            root = Path(directory)

            def command(*args):
                return subprocess.run(
                    args,
                    cwd=PROJECT,
                    capture_output=True,
                    timeout=20,
                )

            def git(*args):
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                    check=True,
                    capture_output=True,
                    timeout=10,
                ).stdout

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (root / "src").mkdir()
            (root / "src/app.py").write_text("value = 1\n")
            git("add", "--", "src/app.py")
            git("commit", "-qm", "baseline")
            git("switch", "-qc", "topic")
            (root / "src/app.py").write_text("value = 2\n")
            git("add", "--", "src/app.py")
            git("commit", "-qm", "change value")

            test = command(
                sys.executable,
                "-m",
                "agentic_devkit.test_proof",
                "run",
                str(root),
                "--",
                sys.executable,
                "-c",
                "raise SystemExit(0)",
            )
            self.assertEqual(test.returncode, 0, test.stderr)

            rejected = command(
                sys.executable,
                "-m",
                "agentic_devkit.handoff_proof",
                "create",
                str(root),
                "--task",
                "Fix the production value regression",
                "--base",
                "main",
                "--allow",
                "docs/",
                "--max-files",
                "2",
                "--max-lines",
                "10",
            )
            self.assertEqual(rejected.returncode, 1, rejected.stderr)
            self.assertEqual(json.loads(rejected.stdout)["state"], "rejected")
            self.assertFalse(
                (root / ".git/agentic-dev-kit/handoff-proof.json").exists()
            )

            created = command(
                sys.executable,
                "-m",
                "agentic_devkit.handoff_proof",
                "create",
                str(root),
                "--task",
                "Fix the production value regression",
                "--base",
                "main",
                "--allow",
                "src/",
                "--max-files",
                "2",
                "--max-lines",
                "10",
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            manifest = json.loads(created.stdout)
            self.assertEqual(manifest["state"], "approved")
            self.assertEqual(manifest["task"], "Fix the production value regression")
            self.assertEqual(manifest["evidence"]["range_scope"]["state"], "approved")
            self.assertEqual(manifest["evidence"]["diff_budget"]["state"], "approved")
            self.assertEqual(manifest["evidence"]["test_proof"]["state"], "valid")
            self.assertNotIn(str(root), created.stdout.decode())

            verified = command(
                sys.executable,
                "-m",
                "agentic_devkit.handoff_proof",
                "verify",
                str(root),
            )
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertEqual(json.loads(verified.stdout)["state"], "valid")

            (root / "src/app.py").write_text("value = 3\n")
            stale = command(
                sys.executable,
                "-m",
                "agentic_devkit.handoff_proof",
                "verify",
                str(root),
            )
            self.assertEqual(stale.returncode, 1, stale.stderr)
            stale_report = json.loads(stale.stdout)
            self.assertEqual(stale_report["state"], "stale")
            self.assertFalse(stale_report["evidence_matches"]["test_proof"])

    def test_malformed_manifest_is_an_explicit_input_error(self):
        with tempfile.TemporaryDirectory(prefix="handoff-proof-test-") as directory:
            root = Path(directory)
            subprocess.run(
                ["git", "init", "-q", "-b", "main", str(root)],
                check=True,
                timeout=10,
            )
            metadata = root / ".git/agentic-dev-kit"
            metadata.mkdir()
            (metadata / "handoff-proof.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "state": "approved",
                        "task": "Example",
                        "policy": {
                            "base": "main",
                            "head": "HEAD",
                            "allow": ["src/"],
                            "max_files": 1,
                            "max_lines": 1,
                            "allow_binary": False,
                        },
                        "evidence": {},
                    }
                )
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_devkit.handoff_proof",
                    "verify",
                    str(root),
                ],
                cwd=PROJECT,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"invalid", result.stderr)
            self.assertNotIn(b"Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
