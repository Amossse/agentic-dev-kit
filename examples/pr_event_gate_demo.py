"""Reproduce a trusted PR event, mismatched checkout, and out-of-scope change."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--installed", action="store_true")
    args = parser.parse_args()
    command = (
        ["pr-event-gate"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.pr_event_gate"]
    )
    with tempfile.TemporaryDirectory(prefix="pr-event-gate-demo-") as directory:
        repo = Path(directory) / "repo"
        repo.mkdir()
        event_file = Path(directory) / "event.json"

        def git(*items):
            return subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *items],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout.strip()

        def check(step, event, expected):
            event_file.write_text(json.dumps(event), encoding="utf-8")
            result = subprocess.run(
                [
                    *command,
                    str(repo),
                    "--event",
                    str(event_file),
                    "--event-name",
                    "pull_request",
                ],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != expected:
                raise RuntimeError(result.stderr)
            report = json.loads(result.stdout) if result.stdout else None
            print(
                json.dumps(
                    {
                        "step": step,
                        "exit": result.returncode,
                        "state": report["state"] if report else "error",
                        "rejected_reasons": report["rejected_reasons"]
                        if report
                        else [],
                    },
                    sort_keys=True,
                )
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (repo / ".agentic-dev-kit").mkdir()
        (repo / "src").mkdir()
        (repo / ".agentic-dev-kit/policy.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "allow": ["src/"],
                    "max_files": 2,
                    "max_lines": 4,
                    "max_file_lines": 4,
                    "allow_binary": False,
                }
            )
        )
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
        check("small_fix", event, 0)
        wrong = {"pull_request": {"base": {"sha": base}, "head": {"sha": base}}}
        check("wrong_checkout", wrong, 2)
        (repo / "docs.md").write_text("unrelated\n")
        git("add", "docs.md")
        git("commit", "-qm", "extra")
        event["pull_request"]["head"]["sha"] = git("rev-parse", "HEAD")
        check("outside_scope", event, 1)


if __name__ == "__main__":
    main()
