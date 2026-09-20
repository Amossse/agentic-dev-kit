"""Acceptance checks for merge-base commit-range scope decisions."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentic_devkit.range_scope import InputError, revision

PROJECT = Path(__file__).resolve().parents[1]


class RangeAcceptance(unittest.TestCase):
    def test_real_history_and_cli(self):
        with tempfile.TemporaryDirectory(prefix="range-scope-test-") as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                    check=True,
                    capture_output=True,
                    timeout=10,
                ).stdout

            def cli(*scopes, base="main", head="topic"):
                before = (
                    git("rev-parse", "HEAD"),
                    git("status", "--porcelain=v1", "-z"),
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.range_scope",
                        str(root),
                        "--base",
                        base,
                        "--head",
                        head,
                        *[f"--allow={scope}" for scope in scopes],
                    ],
                    cwd=PROJECT,
                    capture_output=True,
                    timeout=15,
                )
                self.assertEqual(
                    before,
                    (git("rev-parse", "HEAD"), git("status", "--porcelain=v1", "-z")),
                )
                self.assertNotIn(str(root).encode(), result.stdout + result.stderr)
                return result.returncode, json.loads(
                    result.stdout
                ) if result.stdout else None

            git("init", "-q", "-b", "main")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (root / "src").mkdir()
            (root / "src/payment.py").write_text("value = 1\n")
            git("add", "--", "src/payment.py")
            git("commit", "-qm", "baseline")
            git("switch", "-qc", "topic")
            (root / "src/payment.py").write_text("value = 2\n")
            git("add", "--", "src/payment.py")
            git("commit", "-qm", "payment fix")
            git("branch", "topic-ok")
            (root / ".github/workflows").mkdir(parents=True)
            (root / ".github/workflows/ci.yml").write_text("name: unexpected\n")
            git("add", "--", ".github/workflows/ci.yml")
            git("commit", "-qm", "unexpected CI edit")
            git("switch", "-q", "main")
            (root / "docs").mkdir()
            (root / "docs/base.md").write_text("base moved\n")
            git("add", "--", "docs/base.md")
            git("commit", "-qm", "advance base")

            code, report = cli("src/")
            self.assertEqual((code, report["changed_records"]), (1, 2))
            self.assertEqual(
                [item["path"] for item in report["changes"]],
                [".github/workflows/ci.yml", "src/payment.py"],
            )
            self.assertNotIn(
                "docs/base.md", [item["path"] for item in report["changes"]]
            )
            self.assertEqual(cli("src/", head="topic-ok")[0], 0)
            self.assertEqual(cli("src/", base="main", head="main")[0], 3)
            self.assertEqual(cli("src/", base="missing")[0], 2)
            self.assertEqual(cli("src/", base="--output=/tmp/nope")[0], 2)
            git("config", "diff.renames", "true")
            git("switch", "-q", "topic")
            git("mv", "--", "src/payment.py", "src/renamed.py")
            git("commit", "-qm", "move payment")
            code, report = cli("src/renamed.py")
            self.assertEqual(code, 1)
            self.assertIn(
                "src/payment.py", [item["path"] for item in report["changes"]]
            )

    def test_revision_validation(self):
        for value in (
            "",
            "-x",
            "main..topic",
            "main...topic",
            "two words",
            "a\n",
            "a" * 513,
        ):
            with self.subTest(value=repr(value)), self.assertRaises(InputError):
                revision(value)
        for value in ("HEAD", "main", "HEAD~2", "refs/pull/1/head", "@{upstream}"):
            self.assertEqual(revision(value), value)


if __name__ == "__main__":
    unittest.main()
