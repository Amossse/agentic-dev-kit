"""Check exact-run evidence and malformed or stale GitHub responses."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_devkit.workflow_run_audit import AuditError, fetch

PROJECT = Path(__file__).resolve().parents[1]
RUN = 36281705940
SHA = "034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0"
FIXTURE = json.loads((PROJECT / "examples/workflow_run_success.json").read_text())


class WorkflowRunAuditTest(unittest.TestCase):
    def test_match_reject_pending_and_bad_json(self):
        with tempfile.TemporaryDirectory() as directory:
            snapshot = Path(directory) / "run.json"

            def run():
                return subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.workflow_run_audit",
                        "Amossse/agentic-dev-kit",
                        "--run",
                        str(RUN),
                        "--sha",
                        SHA,
                        "--workflow",
                        ".github/workflows/ci.yml",
                        "--event",
                        "push",
                        "--snapshot",
                        str(snapshot),
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            snapshot.write_text(json.dumps(FIXTURE))
            result = run()
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "matched")
            snapshot.write_text(
                json.dumps({**FIXTURE, "path": ".github/workflows/ci.yml@main"})
            )
            self.assertEqual(run().returncode, 0)
            snapshot.write_text(json.dumps({**FIXTURE, "head_sha": "a" * 40}))
            result = run()
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "rejected")
            snapshot.write_text(
                json.dumps({**FIXTURE, "status": "in_progress", "conclusion": None})
            )
            result = run()
            self.assertEqual(result.returncode, 1, result.stderr)
            snapshot.write_text('{"id":1,"id":2}')
            result = run()
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_api_error_body_is_not_logged(self):
        with patch("agentic_devkit.workflow_run_audit.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = b"token-shaped secret"
            with self.assertRaisesRegex(AuditError, "lookup failed") as error:
                fetch("owner/repo", RUN)
            self.assertNotIn("token-shaped", str(error.exception))


if __name__ == "__main__":
    unittest.main()
