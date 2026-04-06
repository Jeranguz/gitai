from unittest.mock import patch, call, MagicMock
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


def invoke_commit(*args, config=FAKE_CONFIG, suggestions=FAKE_SUGGESTIONS, chosen="feat(cli): add commit command", push_returncode=0):
    """Run `gitai commit [args]` with all external calls mocked."""
    with patch("gitai.cli.get_staged_diff", return_value="+some change"), \
         patch("gitai.cli.is_diff_meaningful", return_value=True), \
         patch("gitai.cli.load_config", return_value=config), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.truncate_diff", return_value=("+some change", False)), \
         patch("gitai.cli.build_commit_prompt") as mock_prompt, \
         patch("gitai.cli.get_commit_suggestions", return_value=suggestions), \
         patch("gitai.cli.questionary.select") as mock_select, \
         patch("gitai.cli.subprocess.run") as mock_subprocess:
        mock_select.return_value.ask.return_value = chosen
        mock_subprocess.return_value = MagicMock(returncode=push_returncode)
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


# --- push error surfacing ---

def test_push_failure_exits_with_error():
    result, _, _ = invoke_commit("--push", push_returncode=1)
    assert result.exit_code != 0


def test_push_failure_prints_error_message():
    result, _, _ = invoke_commit("--push", push_returncode=1)
    assert "Push failed" in result.output


FAKE_PR_DESCRIPTION = "## Title\nfeat: add auth\n## Description\n- added login endpoint"

FAKE_COMMITS = [{"subject": "feat: add thing", "diff": "+code"}]


def invoke_pr(*args, config=FAKE_CONFIG, description=FAKE_PR_DESCRIPTION, push_returncode=0):
    """Run `gitai pr [args]` with all external calls mocked."""
    with patch("gitai.cli.load_config", return_value=config), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.get_branch_name", return_value="feature/foo"), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=FAKE_COMMITS), \
         patch("gitai.cli.get_diff_since_base", return_value="+flat diff"), \
         patch("gitai.cli.truncate_diff", return_value=("+flat diff", False)), \
         patch("gitai.cli.build_pr_prompt") as mock_prompt, \
         patch("gitai.cli.get_pr_description", return_value=description), \
         patch("gitai.cli.subprocess.run") as mock_subprocess:
        mock_subprocess.return_value = MagicMock(returncode=push_returncode)
        result = runner.invoke(app, ["pr", *args])
        return result, mock_subprocess, mock_prompt


# --- gitai pr basic behavior ---

def test_pr_exits_zero_on_success():
    result, _, _ = invoke_pr()
    assert result.exit_code == 0

def test_pr_prints_description():
    result, _, _ = invoke_pr()
    assert "feat: add auth" in result.output

def test_pr_pushes_branch_to_remote():
    _, mock_subprocess, _ = invoke_pr()
    calls = [c.args[0] for c in mock_subprocess.call_args_list]
    assert any(c[:3] == ["git", "push", "-u"] for c in calls)

def test_pr_push_failure_exits_with_error():
    result, _, _ = invoke_pr(push_returncode=1)
    assert result.exit_code != 0

def test_pr_push_failure_prints_error_message():
    result, _, _ = invoke_pr(push_returncode=1)
    assert "Push failed" in result.output


# --- base branch argument ---

def test_pr_passes_explicit_base_branch():
    with patch("gitai.cli.load_config", return_value=FAKE_CONFIG), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.get_branch_name", return_value="feature/foo"), \
         patch("gitai.cli.get_base_branch") as mock_base, \
         patch("gitai.cli.get_commits_since_base", return_value=FAKE_COMMITS), \
         patch("gitai.cli.get_diff_since_base", return_value=""), \
         patch("gitai.cli.truncate_diff", return_value=("", False)), \
         patch("gitai.cli.build_pr_prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_PR_DESCRIPTION), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0)):
        mock_base.return_value = "development"
        runner.invoke(app, ["pr", "development"])
    mock_base.assert_called_once_with("development")

def test_pr_passes_none_when_no_base_branch_given():
    with patch("gitai.cli.load_config", return_value=FAKE_CONFIG), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.get_branch_name", return_value="feature/foo"), \
         patch("gitai.cli.get_base_branch") as mock_base, \
         patch("gitai.cli.get_commits_since_base", return_value=FAKE_COMMITS), \
         patch("gitai.cli.get_diff_since_base", return_value=""), \
         patch("gitai.cli.truncate_diff", return_value=("", False)), \
         patch("gitai.cli.build_pr_prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_PR_DESCRIPTION), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0)):
        mock_base.return_value = "main"
        runner.invoke(app, ["pr"])
    mock_base.assert_called_once_with(None)


# --- --full-diff flag ---

def test_full_diff_flag_uses_get_diff_since_base():
    with patch("gitai.cli.load_config", return_value=FAKE_CONFIG), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.get_branch_name", return_value="feature/foo"), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base") as mock_commits, \
         patch("gitai.cli.get_diff_since_base") as mock_diff, \
         patch("gitai.cli.truncate_diff", return_value=("+flat", False)), \
         patch("gitai.cli.build_pr_prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_PR_DESCRIPTION), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0)):
        mock_diff.return_value = "+flat diff"
        runner.invoke(app, ["pr", "--full-diff"])
    mock_diff.assert_called_once_with("main")
    mock_commits.assert_not_called()


# --- --minimal flag ---

def test_minimal_flag_passes_minimal_mode_to_prompt():
    _, _, mock_prompt = invoke_pr("--minimal")
    assert mock_prompt.call_args.kwargs.get("mode") == "minimal"

def test_no_minimal_flag_passes_default_mode_to_prompt():
    _, _, mock_prompt = invoke_pr()
    assert mock_prompt.call_args.kwargs.get("mode") == "default"


# --- --template flag ---

def test_template_flag_loads_file_content(tmp_path):
    template_file = tmp_path / "template.md"
    template_file.write_text("## Summary\n## Checklist\n")
    with patch("gitai.cli.load_config", return_value=FAKE_CONFIG), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.get_branch_name", return_value="feature/foo"), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=FAKE_COMMITS), \
         patch("gitai.cli.get_diff_since_base", return_value=""), \
         patch("gitai.cli.truncate_diff", return_value=("", False)), \
         patch("gitai.cli.build_pr_prompt") as mock_prompt, \
         patch("gitai.cli.get_pr_description", return_value=FAKE_PR_DESCRIPTION), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0)):
        runner.invoke(app, ["pr", "--template", str(template_file)])
    template_arg = mock_prompt.call_args.kwargs.get("template")
    assert template_arg == "## Summary\n## Checklist\n"
