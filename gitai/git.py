import subprocess
from pathlib import Path

def get_staged_diff() -> str:
    result = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout

def get_repo_name() -> str:
    path = Path.cwd()
    return path.name

def is_diff_meaningful(diff: str) -> bool:
    meaningful_lines = [
        line for line in diff.splitlines()
        if line.startswith(("+", "-"))
        and not line.startswith(("+++", "---"))
        and line.strip() not in ("+", "-", "")
    ]
    return len(meaningful_lines) > 0