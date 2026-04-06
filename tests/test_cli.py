from unittest.mock import patch, call
from typer.testing import CliRunner
from gitai.cli import app

runner = CliRunner()

FAKE_CONFIG = {
    "model": "llama3.2",
    "provider": "ollama",
    "ollama_url": "http://localhost:11434",
    "commit_style": "conventional",
    "emoji": False,
    "num_suggestions": 3,
}

FAKE_SUGGESTIONS = [
    "1. feat(cli): add commit command",
    "2. fix(cli): handle empty diff",
    "3. chore(cli): clean up imports",
]


def invoke_commit(*args, config=FAKE_CONFIG, suggestions=FAKE_SUGGESTIONS, chosen="feat(cli): add commit command"):
    """Run `gitai commit [args]` with all external calls mocked."""
    with patch("gitai.cli.get_staged_diff", return_value="+some change"), \
         patch("gitai.cli.is_diff_meaningful", return_value=True), \
         patch("gitai.cli.load_config", return_value=config), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_commit_prompt") as mock_prompt, \
         patch("gitai.cli.get_commit_suggestions", return_value=suggestions), \
         patch("gitai.cli.questionary.select") as mock_select, \
         patch("gitai.cli.subprocess.run") as mock_subprocess:
        mock_select.return_value.ask.return_value = chosen
        result = runner.invoke(app, ["commit", *args])
        return result, mock_subprocess, mock_prompt


# --- --push flag ---

def test_push_flag_triggers_git_push():
    _, mock_subprocess, _ = invoke_commit("--push")
    calls = [c.args[0] for c in mock_subprocess.call_args_list]
    assert ["git", "push"] in calls


def test_no_push_flag_skips_git_push():
    _, mock_subprocess, _ = invoke_commit()
    calls = [c.args[0] for c in mock_subprocess.call_args_list]
    assert ["git", "push"] not in calls


def test_push_flag_commits_before_pushing():
    _, mock_subprocess, _ = invoke_commit("--push")
    commands = [c.args[0] for c in mock_subprocess.call_args_list]
    commit_idx = next(i for i, c in enumerate(commands) if c[:2] == ["git", "commit"])
    push_idx = next(i for i, c in enumerate(commands) if c == ["git", "push"])
    assert commit_idx < push_idx


def test_push_flag_exits_zero():
    result, _, _ = invoke_commit("--push")
    assert result.exit_code == 0


# --- --suggestions / -n flag ---

def test_suggestions_flag_passes_value_to_prompt():
    _, _, mock_prompt = invoke_commit("--suggestions", "5")
    assert mock_prompt.call_args.kwargs["num_suggestions"] == 5


def test_suggestions_short_flag_passes_value_to_prompt():
    _, _, mock_prompt = invoke_commit("-n", "5")
    assert mock_prompt.call_args.kwargs["num_suggestions"] == 5


def test_suggestions_flag_overrides_config():
    config = {**FAKE_CONFIG, "num_suggestions": 3}
    _, _, mock_prompt = invoke_commit("--suggestions", "7", config=config)
    assert mock_prompt.call_args.kwargs["num_suggestions"] == 7


def test_suggestions_defaults_to_config_value():
    config = {**FAKE_CONFIG, "num_suggestions": 4}
    _, _, mock_prompt = invoke_commit(config=config)
    assert mock_prompt.call_args.kwargs["num_suggestions"] == 4
