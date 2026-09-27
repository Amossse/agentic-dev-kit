"""Exercise exact release-asset hashing without network access."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agentic_devkit.release_asset_audit import AuditError, fetch

PROJECT = Path(__file__).resolve().parents[1]


class ReleaseAssetAuditTest(unittest.TestCase):
    def test_matched_mismatch_and_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            asset = Path(directory) / "LICENSE"
            asset.write_bytes((PROJECT / "LICENSE").read_bytes())

            def run(snapshot: str):
                return subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.release_asset_audit",
                        "owner/repo",
                        "--tag",
                        "v0.8.0",
                        "--snapshot",
                        str(PROJECT / "examples" / snapshot),
                        str(asset),
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

            result = run("release_asset_matched.json")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "matched")
            result = run("release_asset_mismatch.json")
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "rejected")
            malformed = Path(directory) / "malformed.json"
            malformed.write_text(
                '{"tag_name":"v0.8.0","draft":false,"assets":[{"name":"LICENSE","state":"uploaded","size":1064,"digest":null}]}'
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_devkit.release_asset_audit",
                    "owner/repo",
                    "--tag",
                    "v0.8.0",
                    "--snapshot",
                    str(malformed),
                    str(asset),
                ],
                cwd=PROJECT,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            asset.write_bytes(b"changed\n")
            result = run("release_asset_matched.json")
            self.assertEqual(result.returncode, 1, result.stderr)
            asset.unlink()
            result = run("release_asset_matched.json")
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("Traceback", result.stderr)

    def test_failed_api_does_not_leak_error_body(self):
        with patch("agentic_devkit.release_asset_audit.subprocess.run") as run:
            run.return_value.returncode = 1
            run.return_value.stderr = b"secret-looking data"
            with self.assertRaisesRegex(AuditError, "lookup failed") as error:
                fetch("owner/repo", "v0.8.0")
            self.assertNotIn("secret-looking", str(error.exception))


if __name__ == "__main__":
    unittest.main()
