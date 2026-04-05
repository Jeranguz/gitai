from typing import Optional
import typer
import questionary
import subprocess
from gitai.config import load_config, save_config
from gitai.git import get_staged_diff, get_repo_name, is_diff_meaningful
from gitai.prompt import build_commit_prompt
from gitai.ai import get_commit_suggestions
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
            subprocess.run(["git", "push"])
        raise typer.Exit()

    config = load_config()
    repo_name = get_repo_name()
    prompt = build_commit_prompt(diff, repo_name, emoji=config["emoji"], commit_style=config["commit_style"])

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
        subprocess.run(["git", "push"])


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

    new_config = {
        "model": model,
        "provider": provider,
        "ollama_url": ollama_url,
        "commit_style": commit_style,
        "emoji": emoji,
    }

    save_config(new_config)
    typer.echo("\n✅ Config saved to ~/.gitai.toml")


if __name__ == "__main__":
    app()
