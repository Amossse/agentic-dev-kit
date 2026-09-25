"""Exercise PR event binding against disposable Git histories."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class PullRequestEventGateTest(unittest.TestCase):
    def test_event_binding_and_policy(self):
        with tempfile.TemporaryDirectory(prefix="pr-event-gate-test-") as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()

            def git(*args):
                return (
                    subprocess.run(
                        [
                            "git",
                            "-c",
                            "core.hooksPath=/dev/null",
                            "-C",
                            str(repo),
                            *args,
                        ],
                        check=True,
                        capture_output=True,
                        timeout=10,
                    )
                    .stdout.decode()
                    .strip()
                )

            def run(event, name="pull_request"):
                event_path = Path(directory) / "event.json"
                event_path.write_text(json.dumps(event), encoding="utf-8")
                return subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.pr_event_gate",
                        str(repo),
                        "--event",
                        str(event_path),
                        "--event-name",
                        name,
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (repo / ".agentic-dev-kit").mkdir()
            (repo / ".agentic-dev-kit/policy.json").write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "allow": ["src/"],
                        "max_files": 1,
                        "max_lines": 4,
                        "max_file_lines": 4,
                        "allow_binary": False,
                    }
                )
            )
            (repo / "src").mkdir()
            (repo / "src/app.py").write_text("total = 100\n")
            git("add", ".agentic-dev-kit/policy.json", "src/app.py")
            git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")
            git("switch", "-qc", "topic")
            (repo / "src/app.py").write_text("total = 99\n")
            git("add", "src/app.py")
            git("commit", "-qm", "fix")
            head = git("rev-parse", "HEAD")
            event = {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}}

            result = run(event)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["state"], "approved")
            self.assertEqual(run(event, "pull_request_target").returncode, 2)
            self.assertEqual(
                run({"pull_request": {"base": {}, "head": {"sha": head}}}).returncode, 2
            )
            self.assertEqual(
                run(
                    {"pull_request": {"base": {"sha": "main"}, "head": {"sha": head}}}
                ).returncode,
                2,
            )
            self.assertEqual(
                run(
                    {"pull_request": {"base": {"sha": base}, "head": {"sha": base}}}
                ).returncode,
                2,
            )

            (repo / "docs.md").write_text("unrelated\n")
            git("add", "docs.md")
            git("commit", "-qm", "extra")
            event["pull_request"]["head"]["sha"] = git("rev-parse", "HEAD")
            result = run(event)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(
                "outside_scope", json.loads(result.stdout)["rejected_reasons"]
            )

    def test_missing_event_and_duplicate_keys_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="pr-event-gate-test-") as directory:
            event = Path(directory) / "event.json"
            command = [
                sys.executable,
                "-m",
                "agentic_devkit.pr_event_gate",
                "--event-name",
                "pull_request",
            ]
            environment = {**os.environ, "GITHUB_EVENT_PATH": ""}
            result = subprocess.run(
                command, cwd=PROJECT, capture_output=True, env=environment
            )
            self.assertEqual(result.returncode, 2)
            event.write_text('{"pull_request":{},"pull_request":{}}')
            result = subprocess.run(
                [*command, "--event", str(event)], cwd=PROJECT, capture_output=True
            )
            self.assertEqual(result.returncode, 2)
            self.assertNotIn(b"Traceback", result.stderr)
            event.write_bytes(b" " * (1024 * 1024 + 1))
            result = subprocess.run(
                [*command, "--event", str(event)], cwd=PROJECT, capture_output=True
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"exceeds 1 MiB", result.stderr)
