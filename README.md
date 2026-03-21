# gitai

AI-powered git commit message generator. Analyzes your staged changes and suggests meaningful, [Conventional Commits](https://www.conventionalcommits.org/)-formatted commit messages.

## Features

- Reads your staged `git diff` and sends it to an LLM
- Suggests 3 commit messages in Conventional Commits format
- Interactive selection: pick a suggestion or write your own
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
| `provider` | `ollama` | LLM provider (`ollama`) |
| `ollama_url` | `http://localhost:11434` | Base URL for the Ollama API |
| `commit_style` | `conventional` | Commit message style |
| `emoji` | `false` | Prepend emojis to commit messages |

Example `~/.gitai.toml`:

```toml
model = "llama3.2"
provider = "ollama"
ollama_url = "http://localhost:11434"
commit_style = "conventional"
emoji = false
```

## Requirements

- [Ollama](https://ollama.com/) running locally (default provider)
- A model pulled in Ollama, e.g. `ollama pull llama3.2`

## TODO

- [ ] Support additional LLM providers (OpenAI, Anthropic, Gemini, etc.) via [litellm](https://github.com/BerriAI/litellm) — the dependency is already included
- [ ] Improve commit message quality: better prompt engineering, support for different commit styles (e.g. imperative mood enforcement, scope inference from changed files)
- [ ] Allow configuring the number of suggestions generated
- [ ] Add `--push` flag to commit and push in one step
- [ ] Support unstaged changes with an optional `--all` flag