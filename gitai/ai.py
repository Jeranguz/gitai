import litellm
from litellm.exceptions import APIConnectionError, AuthenticationError
from gitai.config import load_config

def get_commit_suggestions(prompt: str) -> list[str]:
    config = load_config()

    provider = config["provider"].lower()
    model = config["model"]
    model_string = f"{provider}/{model}"

    kwargs = {
        "model": model_string,
        "messages": [{"role": "user", "content": prompt}],
    }

    if provider == "ollama":
        kwargs["api_base"] = config["ollama_url"]

    try:
        response = litellm.completion(**kwargs)
    except APIConnectionError:
        if provider == "ollama":
            raise SystemExit(
                f"[gitai] Could not connect to Ollama at {config['ollama_url']}. "
                "Is Ollama running? Try: ollama serve"
            )
        raise SystemExit(
            f"[gitai] Could not connect to the {provider} API. "
            "Check your network connection and try again."
        )
    except AuthenticationError:
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        env_var = key_map.get(provider, f"{provider.upper()}_API_KEY")
        raise SystemExit(
            f"[gitai] Authentication failed for {provider}. "
            f"Set the {env_var} environment variable and try again."
        )

    text = response.choices[0].message.content.strip()

    suggestions = []
    for line in text.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            suggestions.append(line)

    return suggestions


def get_pr_description(prompt: str) -> str:
    config = load_config()

    provider = config["provider"].lower()
    model = config["model"]
    model_string = f"{provider}/{model}"

    kwargs = {
        "model": model_string,
        "messages": [{"role": "user", "content": prompt}],
    }

    if provider == "ollama":
        kwargs["api_base"] = config["ollama_url"]

    try:
        response = litellm.completion(**kwargs)
    except APIConnectionError:
        if provider == "ollama":
            raise SystemExit(
                f"[gitai] Could not connect to Ollama at {config['ollama_url']}. "
                "Is Ollama running? Try: ollama serve"
            )
        raise SystemExit(
            f"[gitai] Could not connect to the {provider} API. "
            "Check your network connection and try again."
        )
    except AuthenticationError:
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GEMINI_API_KEY",
        }
        env_var = key_map.get(provider, f"{provider.upper()}_API_KEY")
        raise SystemExit(
            f"[gitai] Authentication failed for {provider}. "
            f"Set the {env_var} environment variable and try again."
        )

    return response.choices[0].message.content.strip()
