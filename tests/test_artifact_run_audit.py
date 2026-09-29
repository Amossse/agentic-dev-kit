"""Check artifact association and fail-closed API handling."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_devkit.artifact_run_audit import AuditError, fetch_artifact

PROJECT = Path(__file__).resolve().parents[1]
ARTIFACT = json.loads((PROJECT / "examples/artifact_run_matched.json").read_text())


class ArtifactRunAuditTest(unittest.TestCase):
    def test_match_mismatch_expired_and_missing_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact_file = Path(directory) / "artifact.json"

            def run(data):
                artifact_file.write_text(json.dumps(data))
                return subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.artifact_run_audit",
                        "Amossse/agentic-dev-kit",
                        "--artifact",
                        "12345",
                        "--run",
                        "36281705940",
                        "--sha",
                        "034d46bf8d4e4aaa0dd35e433df4e1a55c7d55b0",
                        "--workflow",
                        ".github/workflows/ci.yml",
                        "--event",
                        "push",
                        "--artifact-snapshot",
                        str(artifact_file),
                        "--run-snapshot",
                        str(PROJECT / "examples/workflow_run_success.json"),
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            result = run(ARTIFACT)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "matched")
            for changed in (
                {**ARTIFACT, "expired": True},
                {**ARTIFACT, "workflow_run": {**ARTIFACT["workflow_run"], "id": 9}},
            ):
                result = run(changed)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertEqual(json.loads(result.stdout)["state"], "rejected")
            result = run({**ARTIFACT, "digest": None})
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_api_error_body_is_not_logged(self):
        with patch("agentic_devkit.artifact_run_audit.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = b"token-shaped secret"
            with self.assertRaisesRegex(AuditError, "lookup failed") as error:
                fetch_artifact("owner/repo", 12345)
            self.assertNotIn("token-shaped", str(error.exception))


if __name__ == "__main__":
    unittest.main()
