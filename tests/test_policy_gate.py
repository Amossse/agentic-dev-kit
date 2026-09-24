"""Real Git acceptance checks for base-commit policy enforcement."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]


class PolicyGateAcceptance(unittest.TestCase):
    def test_base_policy_controls_branch_and_rejects_policy_edit(self):
        with tempfile.TemporaryDirectory(prefix="policy-gate-test-") as directory:
            repo = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *args],
                    check=True,
                    capture_output=True,
                    timeout=10,
                ).stdout

            def check(head="HEAD"):
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.policy_gate",
                        str(repo),
                        "--base",
                        "main",
                        "--head",
                        head,
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    timeout=15,
                )
                return result.returncode, json.loads(result.stdout), result.stderr

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (repo / ".agentic-dev-kit").mkdir()
            policy_path = repo / ".agentic-dev-kit/policy.json"
            policy = {
                "schema_version": 1,
                "allow": ["src/"],
                "max_files": 1,
                "max_lines": 4,
                "max_file_lines": 4,
                "allow_binary": False,
            }
            policy_path.write_text(json.dumps(policy))
            (repo / "src").mkdir()
            (repo / "src/app.py").write_text("total = 100\n")
            git("add", "--", ".agentic-dev-kit/policy.json", "src/app.py")
            git("commit", "-qm", "owner policy and baseline")
            self.assertEqual(check("main")[0], 3)

            git("switch", "-qc", "topic")
            (repo / "src/app.py").write_text("total = 99\n")
            git("add", "--", "src/app.py")
            git("commit", "-qm", "small fix")
            code, report, _ = check()
            self.assertEqual(code, 0)
            self.assertEqual(report["state"], "approved")
            self.assertEqual(report["range_scope"]["state"], "approved")
            self.assertEqual(report["diff_budget"]["observed"]["changed_lines"], 2)

            (repo / "docs.md").write_text("Unexpected documentation edit\n")
            git("add", "--", "docs.md")
            git("commit", "-qm", "unrelated documentation")
            code, report, _ = check()
            self.assertEqual(code, 1)
            self.assertIn("outside_scope", report["rejected_reasons"])
            git("revert", "--no-edit", "HEAD")

            (repo / "src/generated.py").write_text(
                "\n".join(f"item_{n}" for n in range(5)) + "\n"
            )
            git("add", "--", "src/generated.py")
            git("commit", "-qm", "oversized generated output")
            code, report, _ = check()
            self.assertEqual(code, 1)
            self.assertIn("budget_exceeded", report["rejected_reasons"])

            policy["allow"] = ["src/", ".agentic-dev-kit/"]
            policy["max_files"] = 100
            policy["max_lines"] = 100
            policy["max_file_lines"] = 100
            policy_path.write_text(json.dumps(policy))
            git("add", "--", ".agentic-dev-kit/policy.json")
            git("commit", "-qm", "attempt to widen policy")
            code, report, _ = check()
            self.assertEqual(code, 1)
            self.assertIn("policy_changed", report["rejected_reasons"])
            self.assertEqual(report["diff_budget"]["budget"]["max_files"], 1)

    def test_missing_policy_is_explicit_error(self):
        with tempfile.TemporaryDirectory(prefix="policy-gate-test-") as directory:
            repo = Path(directory)
            subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
            (repo / "README.md").write_text("no policy\n")
            subprocess.run(["git", "-C", str(repo), "add", "README.md"], check=True)
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Example",
                    "-c",
                    "user.email=example@example.invalid",
                    "-C",
                    str(repo),
                    "commit",
                    "-qm",
                    "baseline",
                ],
                check=True,
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_devkit.policy_gate",
                    str(repo),
                    "--base",
                    "main",
                ],
                cwd=PROJECT,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"policy-gate:", result.stderr)
            self.assertNotIn(b"Traceback", result.stderr)

            (repo / ".agentic-dev-kit").mkdir()
            (repo / ".agentic-dev-kit/policy.json").write_text(
                '{"schema_version":1,"schema_version":1}'
            )
            subprocess.run(
                ["git", "-C", str(repo), "add", ".agentic-dev-kit/policy.json"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-c",
                    "user.name=Example",
                    "-c",
                    "user.email=example@example.invalid",
                    "-C",
                    str(repo),
                    "commit",
                    "-qm",
                    "duplicate policy key",
                ],
                check=True,
            )
            duplicate = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_devkit.policy_gate",
                    str(repo),
                    "--base",
                    "main",
                ],
                cwd=PROJECT,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(duplicate.returncode, 2)
            self.assertIn(b"duplicate JSON keys", duplicate.stderr)


if __name__ == "__main__":
    unittest.main()
