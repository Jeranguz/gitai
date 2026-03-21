import requests
from gitai.config import load_config

def get_commit_suggestions(prompt: str) -> list[str]:
    config = load_config()
    response = requests.post(
        f"{config['ollama_url']}/api/generate",
        json={
            "model": config["model"],
            "prompt": prompt,
            "stream": False,
        }
    )
    response.raise_for_status()
    text = response.json()["response"].strip()

    suggestions = []
    for line in text.splitlines():
        line = line.strip()
        if line and line[0].isdigit() and "." in line:
            suggestions.append(line)

    return suggestions