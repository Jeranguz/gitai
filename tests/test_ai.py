from unittest.mock import patch, MagicMock
import pytest
from gitai.ai import get_commit_suggestions, get_pr_description
from litellm.exceptions import APIConnectionError, AuthenticationError

FAKE_CONFIG_OLLAMA = {
    "provider": "ollama",
    "model": "llama3.2",
    "ollama_url": "http://localhost:11434",
}

FAKE_CONFIG_OPENAI = {
    "provider": "openai",
    "model": "gpt-4o",
    "ollama_url": "http://localhost:11434",
}

FAKE_CONFIG_ANTHROPIC = {
    "provider": "anthropic",
    "model": "claude-haiku-4-5-20251001",
    "ollama_url": "http://localhost:11434",
}


def make_response(text: str):
    response = MagicMock()
    response.choices[0].message.content = text
    return response


# --- suggestion parsing ---

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_parses_three_numbered_suggestions(mock_completion, _):
    mock_completion.return_value = make_response(
        "1. feat(cli): add commit command\n"
        "2. fix(cli): handle empty diff\n"
        "3. chore(cli): clean up imports"
    )
    result = get_commit_suggestions("prompt")
    assert len(result) == 3

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_preserves_full_suggestion_text(mock_completion, _):
    mock_completion.return_value = make_response(
        "1. feat(cli): add commit command\n"
        "2. fix(cli): handle empty diff\n"
        "3. chore(cli): clean up imports"
    )
    result = get_commit_suggestions("prompt")
    assert result[0] == "1. feat(cli): add commit command"
    assert result[1] == "2. fix(cli): handle empty diff"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_ignores_preamble_and_trailing_lines(mock_completion, _):
    mock_completion.return_value = make_response(
        "Here are your suggestions:\n"
        "1. feat(cli): add commit command\n"
        "2. fix(cli): handle empty diff\n"
        "3. chore(cli): clean up imports\n"
        "Hope these help!"
    )
    result = get_commit_suggestions("prompt")
    assert len(result) == 3
    assert all(r[0].isdigit() for r in result)

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_returns_empty_list_when_no_numbered_lines(mock_completion, _):
    mock_completion.return_value = make_response("Nothing useful here.")
    result = get_commit_suggestions("prompt")
    assert result == []

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_strips_whitespace_from_lines(mock_completion, _):
    mock_completion.return_value = make_response(
        "  1. feat(cli): add commit command  \n"
        "  2. fix(cli): handle empty diff  \n"
        "  3. chore(cli): clean up imports  "
    )
    result = get_commit_suggestions("prompt")
    assert result[0] == "1. feat(cli): add commit command"


# --- model string and api_base ---

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_ollama_model_string_format(mock_completion, _):
    mock_completion.return_value = make_response("1. feat: add thing")
    get_commit_suggestions("prompt")
    assert mock_completion.call_args.kwargs["model"] == "ollama/llama3.2"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OPENAI)
@patch("gitai.ai.litellm.completion")
def test_openai_model_string_format(mock_completion, _):
    mock_completion.return_value = make_response("1. feat: add thing")
    get_commit_suggestions("prompt")
    assert mock_completion.call_args.kwargs["model"] == "openai/gpt-4o"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_ollama_passes_api_base(mock_completion, _):
    mock_completion.return_value = make_response("1. feat: add thing")
    get_commit_suggestions("prompt")
    assert mock_completion.call_args.kwargs.get("api_base") == "http://localhost:11434"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OPENAI)
@patch("gitai.ai.litellm.completion")
def test_non_ollama_omits_api_base(mock_completion, _):
    mock_completion.return_value = make_response("1. feat: add thing")
    get_commit_suggestions("prompt")
    assert "api_base" not in mock_completion.call_args.kwargs

@patch("gitai.ai.load_config", return_value={**FAKE_CONFIG_OLLAMA, "provider": "OLLAMA"})
@patch("gitai.ai.litellm.completion")
def test_provider_casing_is_normalized(mock_completion, _):
    mock_completion.return_value = make_response("1. feat: add thing")
    get_commit_suggestions("prompt")
    assert mock_completion.call_args.kwargs["model"].startswith("ollama/")


# --- error handling ---

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_ollama_connection_error_mentions_ollama_serve(mock_completion, _):
    mock_completion.side_effect = APIConnectionError(
        message="connection refused", llm_provider="ollama", model="llama3.2"
    )
    with pytest.raises(SystemExit, match="ollama serve"):
        get_commit_suggestions("prompt")

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_ollama_connection_error_mentions_url(mock_completion, _):
    mock_completion.side_effect = APIConnectionError(
        message="connection refused", llm_provider="ollama", model="llama3.2"
    )
    with pytest.raises(SystemExit, match="localhost:11434"):
        get_commit_suggestions("prompt")

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OPENAI)
@patch("gitai.ai.litellm.completion")
def test_openai_auth_error_suggests_api_key_var(mock_completion, _):
    mock_completion.side_effect = AuthenticationError(
        message="invalid key", llm_provider="openai", model="gpt-4o"
    )
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        get_commit_suggestions("prompt")

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_ANTHROPIC)
@patch("gitai.ai.litellm.completion")
def test_anthropic_auth_error_suggests_api_key_var(mock_completion, _):
    mock_completion.side_effect = AuthenticationError(
        message="invalid key", llm_provider="anthropic", model="claude-haiku-4-5-20251001"
    )
    with pytest.raises(SystemExit, match="ANTHROPIC_API_KEY"):
        get_commit_suggestions("prompt")


# --- get_pr_description ---

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_get_pr_description_returns_raw_text(mock_completion, _):
    mock_completion.return_value = make_response("## Title\nfeat: add login\n## Description\n- added endpoint")
    result = get_pr_description("prompt")
    assert result == "## Title\nfeat: add login\n## Description\n- added endpoint"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_get_pr_description_uses_correct_model_string(mock_completion, _):
    mock_completion.return_value = make_response("## Title\nsome title")
    get_pr_description("prompt")
    assert mock_completion.call_args.kwargs["model"] == "ollama/llama3.2"

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OLLAMA)
@patch("gitai.ai.litellm.completion")
def test_get_pr_description_connection_error_exits(mock_completion, _):
    mock_completion.side_effect = APIConnectionError(
        message="connection refused", llm_provider="ollama", model="llama3.2"
    )
    with pytest.raises(SystemExit, match="ollama serve"):
        get_pr_description("prompt")

@patch("gitai.ai.load_config", return_value=FAKE_CONFIG_OPENAI)
@patch("gitai.ai.litellm.completion")
def test_get_pr_description_auth_error_suggests_env_var(mock_completion, _):
    mock_completion.side_effect = AuthenticationError(
        message="invalid key", llm_provider="openai", model="gpt-4o"
    )
    with pytest.raises(SystemExit, match="OPENAI_API_KEY"):
        get_pr_description("prompt")
