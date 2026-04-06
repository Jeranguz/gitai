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

def truncate_diff(diff: str, max_chars: int = 12000) -> tuple[str, bool]:
    if len(diff) <= max_chars:
        return diff, False
    return diff[:max_chars], True


def get_branch_name() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout.strip()


def get_base_branch(explicit: str | None = None) -> str:
    if explicit:
        return explicit
    for candidate in ["main", "master", "develop"]:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", candidate],
            capture_output=True, text=True, encoding="utf-8",
        )
        if result.returncode == 0:
            return candidate
    raise SystemExit(
        "[gitai] Could not detect base branch. Specify one: gitai pr <branch>"
    )


def get_commits_since_base(base: str) -> list[dict]:
    log = subprocess.run(
        ["git", "log", f"origin/{base}..HEAD", "--format=%H %s"],
        capture_output=True, text=True, encoding="utf-8",
    )
    commits = []
    for line in log.stdout.strip().splitlines():
        if not line:
            continue
        sha, _, subject = line.partition(" ")
        diff = subprocess.run(
            ["git", "show", sha, "--patch", "--no-color"],
            capture_output=True, text=True, encoding="utf-8",
        )
        commits.append({"subject": subject, "diff": diff.stdout})
    return commits


def get_diff_since_base(base: str) -> str:
    result = subprocess.run(
        ["git", "diff", f"origin/{base}...HEAD"],
        capture_output=True, text=True, encoding="utf-8",
    )
    return result.stdout