"""Check required-status decisions using GitHub-shaped snapshots."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_devkit.required_check_audit import AuditError, fetch

PROJECT = Path(__file__).resolve().parents[1]


class RequiredCheckAuditTest(unittest.TestCase):
    def test_api_failure_does_not_claim_missing_protection(self):
        with patch("agentic_devkit.required_check_audit.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = b"token-shaped secret"
            with self.assertRaisesRegex(AuditError, "lookup failed") as error:
                fetch("owner/repo", "main")
            self.assertNotIn("token-shaped", str(error.exception))

    def test_required_missing_and_bad_input(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory) / "protection.json"

            def run():
                return subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.required_check_audit",
                        "owner/repo",
                        "--branch",
                        "main",
                        "--check",
                        "policy",
                        "--snapshot",
                        str(fixture),
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            fixture.write_text(
                json.dumps(
                    {
                        "required_status_checks": {
                            "strict": True,
                            "checks": [{"context": "policy", "app_id": 15368}],
                            "contexts": ["policy"],
                        },
                        "enforce_admins": {"enabled": True},
                    }
                )
            )
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "required")
            fixture.write_text(
                '{"required_status_checks":{"checks":[{"context":"build"}]}}'
            )
            result = run()
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "not_required")
            fixture.write_text(
                '{"required_status_checks":{},"required_status_checks":{}}'
            )
            result = run()
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
