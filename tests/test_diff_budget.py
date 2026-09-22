"""Acceptance checks for merge-base review-size budgets."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentic_devkit.diff_budget import InputError, limit, numstat_records

PROJECT = Path(__file__).resolve().parents[1]


class DiffBudgetAcceptance(unittest.TestCase):
    def test_real_history_text_binary_and_rename(self):
        with tempfile.TemporaryDirectory(prefix="diff-budget-test-") as directory:
            root = Path(directory)

            def git(*args):
                return subprocess.run(
                    ["git", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
                    check=True,
                    capture_output=True,
                    timeout=10,
                ).stdout

            def cli(*extra, base="main", head="topic", files=2, lines=8):
                before = (
                    git("rev-parse", "HEAD"),
                    git("status", "--porcelain=v1", "-z"),
                )
                result = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.diff_budget",
                        str(root),
                        "--base",
                        base,
                        "--head",
                        head,
                        "--max-files",
                        str(files),
                        "--max-lines",
                        str(lines),
                        *extra,
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
            (root / "src/payment.py").write_text("fee = 1\ntotal = 100\n")
            git("add", "--", "src/payment.py")
            git("commit", "-qm", "baseline")
            git("switch", "-qc", "topic")
            (root / "src/payment.py").write_text("fee = 1\ntotal = 99\n")
            git("add", "--", "src/payment.py")
            git("commit", "-qm", "payment fix")
            git("branch", "topic-small")
            (root / "src/generated.py").write_text(
                "\n".join(f"item_{n} = {n}" for n in range(6)) + "\n"
            )
            git("add", "--", "src/generated.py")
            git("commit", "-qm", "unexpected generated file")
            git("switch", "-q", "main")
            (root / "docs").mkdir()
            (root / "docs/base.md").write_text("base advanced\n")
            git("add", "--", "docs/base.md")
            git("commit", "-qm", "advance base")

            code, result = cli(files=1, lines=4)
            self.assertEqual(code, 1)
            self.assertEqual(result["rejected_reasons"], ["file_limit", "line_limit"])
            self.assertNotIn(
                "docs/base.md", [item["path"] for item in result["changes"]]
            )
            self.assertEqual(
                cli(base="main", head="topic-small", files=1, lines=4)[0], 0
            )
            self.assertEqual(
                cli(
                    "--max-file-lines",
                    "1",
                    base="main",
                    head="topic-small",
                    files=1,
                    lines=4,
                )[1]["rejected_reasons"],
                ["per_file_line_limit"],
            )
            self.assertEqual(cli(base="main", head="main", files=1, lines=4)[0], 3)

            git("switch", "-q", "topic-small")
            (root / "image.bin").write_bytes(bytes(range(256)))
            git("add", "--", "image.bin")
            git("commit", "-qm", "binary asset")
            self.assertEqual(
                cli(head="HEAD", files=3, lines=20)[1]["rejected_reasons"],
                ["binary_files"],
            )
            self.assertEqual(
                cli("--allow-binary", head="HEAD", files=3, lines=20)[0], 0
            )

            git("config", "diff.renames", "true")
            git("mv", "src/payment.py", "src/renamed.py")
            git("commit", "-qm", "rename payment")
            code, result = cli("--allow-binary", head="HEAD", files=2, lines=20)
            self.assertEqual(code, 1)
            self.assertIn("file_limit", result["rejected_reasons"])
            self.assertEqual(result["observed"]["files"], 3)

    def test_input_validation_and_framing(self):
        for value in (-1, 1_000_000_001):
            with self.subTest(value=value), self.assertRaises(InputError):
                limit("--max-lines", value)
        self.assertEqual(limit("--max-lines", 0), 0)
        with self.assertRaises(InputError):
            numstat_records(b"1\t2\tmissing-nul")
        with self.assertRaises(InputError):
            numstat_records(b"x\t2\tfile\0")
        self.assertEqual(numstat_records(b"-\t-\timage.bin\0")[0]["binary"], True)


if __name__ == "__main__":
    unittest.main()
