# gitai

<p align="center">
  <img src="assets/commit-genie.png" alt="The Commit Genie" width="200"/>
</p>

<p align="center">
  <a href="https://pypi.org/project/gitai"><img src="https://img.shields.io/pypi/v/gitai" alt="PyPI version"/></a>
  <a href="https://pypi.org/project/gitai"><img src="https://img.shields.io/pypi/pyversions/gitai" alt="Python versions"/></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT license"/></a>
</p>

AI-powered git commit message generator. Analyzes your staged changes and suggests meaningful commit messages — using any LLM you already have access to.

## Features

- Reads your staged `git diff` and generates 3 commit message suggestions
- Interactive selection: pick a suggestion or write your own
- Supports multiple providers: Ollama (local), OpenAI, Anthropic, Gemini, and [more](https://docs.litellm.ai/docs/providers)
- Two commit styles: [Conventional Commits](https://www.conventionalcommits.org/) or free-form
- Optional emoji (gitmoji) support

## Installation

```bash
pip install gitai
```

Requires Python 3.11+.

## Quick start

```bash
# 1. Stage your changes
git add .

# 2. Run gitai
gitai commit
```

gitai reads the diff, calls your configured LLM, and presents 3 suggestions to choose from.

## Usage

```
gitai commit      Generate commit message suggestions for staged changes
gitai config      View and update settings
gitai --version   Show version
gitai --help      Show help
```

## Configuration

Run `gitai config` to update settings interactively. Settings are stored in `~/.gitai.toml`.

| Key | Default | Description |
|---|---|---|
| `provider` | `ollama` | LLM provider |
| `model` | `llama3.2` | Model name |
| `ollama_url` | `http://localhost:11434` | Ollama API base URL (Ollama only) |
| `commit_style` | `conventional` | `conventional` or `free-form` |
| `emoji` | `false` | Prefix suggestions with gitmoji |

### Supported providers

| Provider | `provider` value | Example `model` value | API key env var |
|---|---|---|---|
| Ollama (local) | `ollama` | `llama3.2`, `mistral` | — |
| Anthropic | `anthropic` | `claude-sonnet-4-6`, `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY` |
| Gemini | `gemini` | `gemini-2.0-flash` | `GEMINI_API_KEY` |

For cloud providers, set the API key in your shell profile:

**bash/zsh** (`~/.bashrc` or `~/.zshrc`):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**PowerShell** (`$PROFILE`):
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

### Example `~/.gitai.toml`

```toml
provider = "anthropic"
model = "claude-haiku-4-5-20251001"
commit_style = "conventional"
emoji = false
ollama_url = "http://localhost:11434"
```

## Local setup (Ollama)

If you want to run fully offline with Ollama:

1. Install [Ollama](https://ollama.com/)
2. Pull a model: `ollama pull llama3.2`
3. Run `gitai commit` — no API key needed

## TODO

- [ ] Allow configuring the number of suggestions generated
- [ ] Add `--push` flag to commit and push in one step
- [ ] Support unstaged changes with an optional `--all` flag
