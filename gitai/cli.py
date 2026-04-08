from typing import Optional
from pathlib import Path
import typer
import questionary
import subprocess
from gitai.config import load_config, save_config
from gitai.git import (
    get_staged_diff, get_repo_name, is_diff_meaningful,
    truncate_diff, get_branch_name, get_base_branch,
    get_commits_since_base, get_diff_since_base,
)
from gitai.prompt import build_commit_prompt, build_pr_prompt
from gitai.ai import get_commit_suggestions, get_pr_description
from gitai import __version__

VALID_PROVIDERS = {"ollama", "openai", "anthropic", "gemini"}
VALID_COMMIT_STYLES = {"conventional", "free-form"}

app = typer.Typer()


def _version_callback(value: bool):
    if value:
        typer.echo(f"gitai {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None, "--version", "-V",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
):
    """AI-powered git commit message generator."""


@app.command()
def commit(
    push: bool = typer.Option(False, "--push", help="Push to remote after committing."),
    suggestions: Optional[int] = typer.Option(
        None, "--suggestions", "-n",
        help="Number of commit message suggestions to generate.",
        min=1,
    ),
):
    """Generate AI-powered commit message suggestions for staged changes."""
    typer.echo("🔍 Reading your git diff...")

    diff = get_staged_diff()
    if not diff:
        typer.echo("No staged changes found. Please stage your changes before committing.")
        raise typer.Exit(code=1)

    if not is_diff_meaningful(diff):
        typer.echo("Staged file appears to be empty or has no content changes.")
        chosen = typer.prompt("Enter your commit message")
        subprocess.run(["git", "commit", "-m", chosen])
        typer.echo(f"\n Committed: {chosen}")
        if push:
            typer.echo("Pushing to remote...")
            push_result = subprocess.run(["git", "push"])
            if push_result.returncode != 0:
                typer.echo("[gitai] Push failed. Check your remote configuration and try again.")
                raise typer.Exit(code=1)
        raise typer.Exit()

    config = load_config()
    max_chars = config.get("max_diff_chars", 12000)
    diff, was_truncated = truncate_diff(diff, max_chars)
    if was_truncated:
        typer.echo("⚠️  Diff truncated to fit model context. Consider committing in smaller chunks.")
    num_suggestions = suggestions if suggestions is not None else config.get("num_suggestions", 3)
    repo_name = get_repo_name()
    prompt = build_commit_prompt(diff, repo_name, emoji=config["emoji"], commit_style=config["commit_style"], num_suggestions=num_suggestions)

    typer.echo("Generating commit message suggestions...")
    suggestions = get_commit_suggestions(prompt)

    if not suggestions:
        typer.echo("No suggestions generated. Please try again.")
        raise typer.Exit()

    clean = [s.split(". ", 1)[1] if ". " in s else s for s in suggestions]
    clean.append("Write my own")

    chosen = questionary.select(
        "Choose a commit message:",
        choices=clean
    ).ask()

    if chosen is None:
        typer.echo("Aborted.")
        raise typer.Exit()

    if chosen == "Write my own":
        chosen = typer.prompt("Enter your custom commit message")

    subprocess.run(["git", "commit", "-m", chosen])
    typer.echo(f"\n Committed: {chosen}")
    if push:
        typer.echo("Pushing to remote...")
        push_result = subprocess.run(["git", "push"])
        if push_result.returncode != 0:
            typer.echo("[gitai] Push failed. Check your remote configuration and try again.")
            raise typer.Exit(code=1)


def _parse_pr_title_body(description: str) -> tuple[str, str]:
    """Extract title and body from PR description in the format:

    ## Title
    <title>

    ## Description
    <body>
    """
    lines = description.splitlines()
    title = ""
    body_start = 0  # fallback: treat entire input as body if ## Title not found
    for i, line in enumerate(lines):
        if line.strip() == "## Title":
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    title = lines[j].strip()
                    body_start = j + 1
                    break
            break
    body = "\n".join(lines[body_start:]).strip()
    return title, body


@app.command()
def pr(
    base_branch: Optional[str] = typer.Argument(
        None,
        help="Base branch to compare against. Auto-detects main/master/develop if omitted.",
    ),
    full_diff: bool = typer.Option(
        False, "--full-diff",
        help="Use flat diff instead of per-commit breakdown.",
    ),
    minimal: bool = typer.Option(
        False, "--minimal",
        help="Output title + bullet list only.",
    ),
    template: Optional[str] = typer.Option(
        None, "--template",
        help="Path to a PR template file.",
    ),
):
    """Push the current branch and generate a ready-to-copy PR title and description."""
    config = load_config()
    repo_name = get_repo_name()

    branch = get_branch_name()
    typer.echo(f"Pushing branch '{branch}' to remote...")
    push_result = subprocess.run(["git", "push", "-u", "origin", branch])
    if push_result.returncode != 0:
        typer.echo("[gitai] Push failed. Check your remote configuration and try again.")
        raise typer.Exit(code=1)

    base = get_base_branch(base_branch)

    if full_diff:
        diff = get_diff_since_base(base)
        max_chars = config.get("max_diff_chars", 12000)
        diff, was_truncated = truncate_diff(diff, max_chars)
        if was_truncated:
            typer.echo("⚠️  Diff truncated to fit model context.")
        commits = []
    else:
        commits = get_commits_since_base(base)
        diff = ""

    template_content = None
    if template:
        template_content = Path(template).read_text(encoding="utf-8")
    else:
        auto_template = Path(".github/PULL_REQUEST_TEMPLATE.md")
        if auto_template.exists():
            template_content = auto_template.read_text(encoding="utf-8")

    mode = "minimal" if minimal else "default"
    prompt = build_pr_prompt(commits, diff, repo_name, mode=mode, template=template_content)

    typer.echo("Generating PR description...")
    description = get_pr_description(prompt)

    typer.echo("\n" + description)


@app.command()
def config():
    """View and update gitai settings."""
    current = load_config()

    typer.echo("Current configuration:\n")
    for key, value in current.items():
        typer.echo(f"  {key}: {value}")

    typer.echo("")
    if not typer.confirm("Do you want to change any settings?"):
        raise typer.Exit()

    provider = typer.prompt(
        "Provider (ollama, openai, anthropic, gemini)",
        default=current["provider"],
    )
    if provider not in VALID_PROVIDERS:
        typer.echo(f"[gitai] Unknown provider '{provider}'. Choose from: {', '.join(sorted(VALID_PROVIDERS))}")
        raise typer.Exit(code=1)

    model = typer.prompt("Model name", default=current["model"])

    ollama_url = current["ollama_url"]
    if provider == "ollama":
        ollama_url = typer.prompt("Ollama URL", default=current["ollama_url"])

    commit_style = typer.prompt(
        "Commit style (conventional, free-form)",
        default=current["commit_style"],
    )
    if commit_style not in VALID_COMMIT_STYLES:
        typer.echo(f"[gitai] Unknown commit style '{commit_style}'. Choose from: {', '.join(sorted(VALID_COMMIT_STYLES))}")
        raise typer.Exit(code=1)

    emoji = typer.confirm("Use emojis in commit messages?", default=current["emoji"])

    num_suggestions = typer.prompt(
        "Number of suggestions to generate",
        default=current.get("num_suggestions", 3),
        type=int,
    )
    if num_suggestions < 1:
        typer.echo("[gitai] num_suggestions must be at least 1.")
        raise typer.Exit(code=1)

    new_config = {
        "model": model,
        "provider": provider,
        "ollama_url": ollama_url,
        "commit_style": commit_style,
        "emoji": emoji,
        "num_suggestions": num_suggestions,
        "max_diff_chars": current.get("max_diff_chars", 12000),
    }

    save_config(new_config)
    typer.echo("\n✅ Config saved to ~/.gitai.toml")


if __name__ == "__main__":
    app()
