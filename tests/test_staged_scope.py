"""Acceptance checks against real Git indexes, including an unmerged index."""

import base64
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from agentic_devkit.staged_scope import InputError, allow_paths, records

PROJECT = Path(__file__).resolve().parents[1]


class Acceptance(unittest.TestCase):
    def test_real_git_and_cli(self):
        with tempfile.TemporaryDirectory(prefix="staged-scope-test-") as directory:
            root = Path(directory)

            def git(*args, data=None):
                return subprocess.run(
                    ["git", "-C", str(root), *args],
                    input=data,
                    capture_output=True,
                    check=True,
                    timeout=10,
                ).stdout

            def cli(*scopes, cwd=None, env=None):
                index_before = (root / ".git/index").read_bytes()
                completed = subprocess.run(
                    [
                        sys.executable,
                        "-m",
                        "agentic_devkit.staged_scope",
                        str(cwd or root),
                        *[f"--allow={scope}" for scope in scopes],
                    ],
                    cwd=PROJECT,
                    env=env,
                    capture_output=True,
                    timeout=15,
                )
                self.assertEqual(index_before, (root / ".git/index").read_bytes())
                self.assertNotIn(
                    str(root).encode(), completed.stdout + completed.stderr
                )
                return completed.returncode, json.loads(completed.stdout)

            git("init", "-q")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@example.invalid")
            (root / "src").mkdir()
            (root / "src/payment.py").write_text("value = 1\n")
            git("add", "--", "src/payment.py")
            # An unborn HEAD must still report the initial staged addition.
            code, report = cli("src/")
            self.assertEqual((code, report["changes"][0]["status"]), (0, "A"))
            git("commit", "-qm", "fixture baseline")
            (root / "src/payment.py").write_text("value = 2\n")
            (root / "untracked.txt").write_text("never staged\n")
            self.assertEqual(cli("src/")[0], 3)
            git("add", "--", "src/payment.py")
            # Later unstaged content cannot change the staged path decision.
            (root / "src/payment.py").write_text("value = 3\n")
            code, report = cli("src/payment.py", cwd=root / "src")
            self.assertEqual((code, report["changed_records"]), (0, 1))
            self.assertEqual(report["changes"][0]["status"], "M")
            self.assertEqual(cli("Src/")[0], 1)
            self.assertEqual(cli("src/payment")[0], 1)
            self.assertEqual(cli("src/")[1], cli("src/", "src/")[1])

            (root / "src2").mkdir()
            (root / "src2/sibling.py").write_text("other = True\n")
            git("add", "--", "src2/sibling.py")
            self.assertEqual(cli("src/")[1]["rejected_records"], 1)
            git("commit", "-qm", "fixture additions")
            head_before_checks = git("rev-parse", "HEAD")
            linked = root / "linked"
            git("worktree", "add", "--detach", str(linked), "HEAD")
            self.assertEqual(cli("src/", cwd=linked)[0], 3)
            (linked / "src/payment.py").write_text("value = 4\n")
            git("-C", str(linked), "add", "--", "src/payment.py")
            self.assertEqual(cli("src/", cwd=linked / "src")[0], 0)
            git("config", "diff.renames", "copies")
            git("mv", "--", "src/payment.py", "src2/renamed.py")
            code, report = cli("src2/")
            self.assertEqual(code, 1)
            self.assertIn(
                ("src/payment.py", "D"),
                [(x["path"], x["status"]) for x in report["changes"]],
            )
            self.assertEqual(cli("src/", "src2/")[0], 0)

            # NUL records must preserve tabs, newlines, Unicode and dash-leading names.
            names = [
                "src/tab\tname.py",
                "src/line\nname.py",
                "src/支付.py",
                "-option.py",
            ]
            for name in names:
                (root / name).write_text("example = 1\n")
                git("add", "--", name)
            # APFS rejects non-UTF-8 filenames; create this index record directly.
            blob = git("rev-parse", "HEAD:src/payment.py").strip()
            raw_name = b"src/raw-\xff.py"
            git(
                "update-index",
                "-z",
                "--index-info",
                data=b"100644 " + blob + b"\t" + raw_name + b"\0",
            )
            code, report = cli("src/", "src2/", "-option.py")
            self.assertEqual(code, 0)
            exact = {base64.b64decode(x["path_bytes_b64"]) for x in report["changes"]}
            self.assertTrue({os.fsencode(name) for name in names} <= exact)
            self.assertIn(raw_name, exact)

            marker = root / "should-not-exist"
            git("config", "core.fsmonitor", f"touch {marker}")
            git("config", "diff.external", f"touch {marker}")
            env = dict(
                os.environ, GIT_INDEX_FILE=str(root / "wrong-index"), GIT_DIR="/missing"
            )
            self.assertEqual(cli("src/", "src2/", "-option.py", env=env)[0], 0)
            self.assertFalse(marker.exists())
            git("config", "--unset", "core.fsmonitor")
            git("config", "--unset", "diff.external")
            self.assertEqual(head_before_checks, git("rev-parse", "HEAD"))
            self.assertEqual((root / "src2/renamed.py").read_text(), "value = 3\n")

            blob = git("rev-parse", "HEAD:src/payment.py").strip()
            path = b"conflict.py"
            data = b""
            for stage in (1, 2, 3):
                data += (
                    b"100644 "
                    + blob
                    + b" "
                    + str(stage).encode()
                    + b"\t"
                    + path
                    + b"\n"
                )
            git("update-index", "--index-info", data=data)
            code, report = cli("src/", "src2/", "-option.py", "conflict.py")
            self.assertEqual(code, 1)
            self.assertTrue(
                any(x["rejected_reason"] == "unmerged" for x in report["changes"])
            )

    def test_validation_and_framing(self):
        for value in (
            "",
            "/",
            "/tmp/a",
            "../a",
            "a/../b",
            "./a",
            "a//b",
            "a//",
            "C:/a",
            "a\\b",
            "src/*",
            "a?",
            "a[0]",
            "a\n",
            "a\x00",
            "\udcff",
        ):
            with self.subTest(value=repr(value)), self.assertRaises(InputError):
                allow_paths([value])
        invalid_values: list[list[str]] = [[], ["a"] * 101, ["a" * 4097]]
        for values in invalid_values:
            with self.assertRaises(InputError):
                allow_paths(values)
        for raw in (
            b"M\0a",
            b"M\0",
            b"R100\0a\0b\0",
            b"X\0a\0",
            b"M\0../a\0",
            b"M\0/a\0",
            b"M\0a//b\0",
            b"A\0a\0" * 10001,
        ):
            with self.subTest(raw=raw[:30]), self.assertRaises(InputError):
                records(raw)
        self.assertEqual(
            records(b"T\0link\0D\0gone\0"), [(b"gone", "D"), (b"link", "T")]
        )
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "agentic_devkit.staged_scope",
                    directory,
                    "--allow",
                    "src/",
                ],
                cwd=PROJECT,
                capture_output=True,
                timeout=15,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(result.stdout, b"")
            self.assertNotIn(directory.encode(), result.stderr)


if __name__ == "__main__":
    unittest.main()
