import typer
import questionary
import subprocess
from gitai.config import load_config, save_config
from gitai.git import get_staged_diff, get_repo_name, is_diff_meaningful
from gitai.prompt import build_commit_prompt
from gitai.ai import get_commit_suggestions

app = typer.Typer(invoke_without_command=True)

@app.command()
def commit():
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
        raise typer.Exit()

    repo_name = get_repo_name()
    prompt = build_commit_prompt(diff, repo_name)

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

@app.command()
def config():
    """View and update gitai settings."""
    current = load_config()

    typer.echo("Current configuration:\n")
    for key, value in current.items():
        typer.echo(f" {key}: {value}")

    typer.echo("")
    if not typer.confirm("Do you want to change any settings?"):
        raise typer.Exit()
    
    model = typer.prompt("Model name", default=current["model"])
    ollama_url = typer.prompt("Ollama URL", default=current["ollama_url"])
    emoji = typer.confirm("Use emojis in commit messages?", default=current["emoji"])

    new_config = {
        "model": model,
        "ollama_url": ollama_url,
        "emoji": emoji,
    }

    save_config(new_config)
    typer.echo("\n✅ Config saved to ~/.gitai.toml")
    
if __name__ == "__main__":
    app()