"""Show a base-owned policy approving, rejecting, and resisting a branch edit."""

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
        ["policy-gate"]
        if args.installed
        else [sys.executable, "-m", "agentic_devkit.policy_gate"]
    )
    with tempfile.TemporaryDirectory(prefix="policy-gate-demo-") as directory:
        repo = Path(directory)

        def git(*items):
            subprocess.run(
                ["git", "-c", "core.hooksPath=/dev/null", "-C", str(repo), *items],
                check=True,
                capture_output=True,
                timeout=10,
            )

        def check(step: str, expected: int):
            result = subprocess.run(
                [*command, str(repo), "--base", "main", "--head", "HEAD"],
                cwd=Path(__file__).resolve().parents[1],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode != expected:
                raise RuntimeError(result.stderr)
            report = json.loads(result.stdout)
            print(
                json.dumps(
                    {
                        "step": step,
                        "exit": result.returncode,
                        "state": report["state"],
                        "rejected_reasons": report["rejected_reasons"],
                    },
                    sort_keys=True,
                )
            )

        git("init", "-q", "-b", "main")
        git("config", "user.name", "Example")
        git("config", "user.email", "example@example.invalid")
        (repo / ".agentic-dev-kit").mkdir()
        policy_file = repo / ".agentic-dev-kit/policy.json"
        policy = {
            "schema_version": 1,
            "allow": ["src/"],
            "max_files": 1,
            "max_lines": 4,
            "max_file_lines": 4,
            "allow_binary": False,
        }
        policy_file.write_text(json.dumps(policy))
        (repo / "src").mkdir()
        (repo / "src/payment.py").write_text("total = 100\n")
        git("add", "--", ".agentic-dev-kit/policy.json", "src/payment.py")
        git("commit", "-qm", "owner policy and baseline")
        git("switch", "-qc", "topic")
        (repo / "src/payment.py").write_text("total = 99\n")
        git("add", "--", "src/payment.py")
        git("commit", "-qm", "payment fix")
        check("small_fix", 0)

        (repo / "src/generated.py").write_text(
            "\n".join(f"item_{n}" for n in range(5)) + "\n"
        )
        git("add", "--", "src/generated.py")
        git("commit", "-qm", "generated output")
        check("oversized", 1)

        policy["allow"] = ["src/", ".agentic-dev-kit/"]
        policy["max_files"] = 100
        policy["max_lines"] = 100
        policy["max_file_lines"] = 100
        policy_file.write_text(json.dumps(policy))
        git("add", "--", ".agentic-dev-kit/policy.json")
        git("commit", "-qm", "widen policy in topic")
        check("policy_edit", 1)


if __name__ == "__main__":
    main()
