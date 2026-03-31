# gitai

<p align="center">
  <img src="assets/commit-genie.png" alt="The Commit Genie" width="200"/>
</p>

AI-powered git commit message generator. Analyzes your staged changes and suggests meaningful, [Conventional Commits](https://www.conventionalcommits.org/)-formatted commit messages.

## Features

- Reads your staged `git diff` and sends it to an LLM
- Suggests 3 commit messages in Conventional Commits format
- Interactive selection: pick a suggestion or write your own
- Supports multiple providers: Ollama (local), OpenAI, Anthropic, Gemini, and [more](https://docs.litellm.ai/docs/providers)
- Configurable model, provider, and commit style
- Optional emoji support in commit messages

## Installation

Requires Python 3.11+.

```bash
pip install .
```

Or, for development:

```bash
pip install -e .
```

## Usage

### Generate a commit message

Stage your changes, then run:

```bash
gitai commit
```

gitai will read the diff, call the configured LLM, and present you with 3 commit message suggestions to choose from.

### View / update configuration

```bash
gitai config
```

Settings are stored in `~/.gitai.toml`.

## Configuration

| Key | Default | Description |
|---|---|---|
| `model` | `llama3.2` | Model name to use |
| `provider` | `ollama` | LLM provider (see supported providers below) |
| `ollama_url` | `http://localhost:11434` | Base URL for the Ollama API (Ollama only) |
| `commit_style` | `conventional` | Commit message style |
| `emoji` | `false` | Prepend emojis to commit messages |

### Supported providers

| Provider | `provider` value | Example `model` value | API key env var |
|---|---|---|---|
| Ollama (local) | `ollama` | `llama3.2`, `mistral` | — |
| Anthropic | `anthropic` | `claude-sonnet-4-6`, `claude-haiku-4-5-20251001` | `ANTHROPIC_API_KEY` |
| OpenAI | `openai` | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY` |
| Gemini | `gemini` | `gemini-2.0-flash` | `GEMINI_API_KEY` |

For cloud providers, set the relevant key in your shell profile:

**bash/zsh** (`~/.bashrc` or `~/.zshrc`):
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

**PowerShell** (`$PROFILE`):
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

Example `~/.gitai.toml` using Anthropic:

```toml
model = "claude-haiku-4-5-20251001"
provider = "anthropic"
ollama_url = "http://localhost:11434"
commit_style = "conventional"
emoji = false
```

## Requirements

- Python 3.11+
- For Ollama: [Ollama](https://ollama.com/) running locally and a model pulled, e.g. `ollama pull llama3.2`
- For cloud providers: the relevant API key set as an environment variable

## TODO

- [ ] Improve commit message quality: better prompt engineering, support for different commit styles (e.g. imperative mood enforcement, scope inference from changed files)
- [ ] Allow configuring the number of suggestions generated
- [ ] Add `--push` flag to commit and push in one step
- [ ] Support unstaged changes with an optional `--all` flag