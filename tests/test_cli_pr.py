import shutil
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner
from gitai.cli import app, _parse_pr_title_body

runner = CliRunner()

FAKE_DESCRIPTION = """## Title
add login feature

## Description
Adds login via OAuth.

### Changes
- add OAuth flow
"""


def _base_config():
    return {
        "provider": "ollama", "model": "llama3.2", "ollama_url": "http://localhost:11434",
        "commit_style": "conventional", "emoji": False, "num_suggestions": 3, "max_diff_chars": 12000,
    }


def test_draft_without_create_exits():
    result = runner.invoke(app, ["pr", "--draft"])
    assert result.exit_code != 0
    assert "--draft requires --create" in result.output


def test_create_declined_does_not_call_cli():
    with patch("gitai.cli.get_branch_name", return_value="feature/login"), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0, stdout="")), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=[{"subject": "s", "diff": "d"}]), \
         patch("gitai.cli.load_config", return_value=_base_config()), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_pr_prompt", return_value="prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_DESCRIPTION):
        result = runner.invoke(app, ["pr", "--create"], input="n\n")
    assert result.exit_code == 0
    assert "https://github.com" not in result.output


def test_create_github_calls_gh():
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stdout="https://github.com/user/repo/pull/1\n")

    with patch("gitai.cli.get_branch_name", return_value="feature/login"), \
         patch("gitai.cli.subprocess.run", side_effect=fake_run), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=[{"subject": "s", "diff": "d"}]), \
         patch("gitai.cli.load_config", return_value=_base_config()), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_pr_prompt", return_value="prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_DESCRIPTION), \
         patch("gitai.cli.get_remote_provider", return_value="github"), \
         patch("gitai.cli.shutil.which", return_value="/usr/bin/gh"):
        result = runner.invoke(app, ["pr", "--create"], input="y\n")

    gh_calls = [c for c in captured if c and c[0] == "gh"]
    assert len(gh_calls) == 1
    assert gh_calls[0][:3] == ["gh", "pr", "create"]
    assert "--title" in gh_calls[0]
    assert "add login feature" in gh_calls[0]
    assert "--draft" not in gh_calls[0]
    assert "https://github.com/user/repo/pull/1" in result.output


def test_create_github_draft_passes_flag():
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stdout="https://github.com/user/repo/pull/1\n")

    with patch("gitai.cli.get_branch_name", return_value="feature/login"), \
         patch("gitai.cli.subprocess.run", side_effect=fake_run), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=[{"subject": "s", "diff": "d"}]), \
         patch("gitai.cli.load_config", return_value=_base_config()), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_pr_prompt", return_value="prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_DESCRIPTION), \
         patch("gitai.cli.get_remote_provider", return_value="github"), \
         patch("gitai.cli.shutil.which", return_value="/usr/bin/gh"):
        runner.invoke(app, ["pr", "--create", "--draft"], input="y\n")

    gh_calls = [c for c in captured if c and c[0] == "gh"]
    assert "--draft" in gh_calls[0]


def test_create_gitlab_calls_glab():
    captured = []

    def fake_run(cmd, **kwargs):
        captured.append(cmd)
        return MagicMock(returncode=0, stdout="https://gitlab.com/user/repo/-/merge_requests/1\n")

    with patch("gitai.cli.get_branch_name", return_value="feature/login"), \
         patch("gitai.cli.subprocess.run", side_effect=fake_run), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=[{"subject": "s", "diff": "d"}]), \
         patch("gitai.cli.load_config", return_value=_base_config()), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_pr_prompt", return_value="prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_DESCRIPTION), \
         patch("gitai.cli.get_remote_provider", return_value="gitlab"), \
         patch("gitai.cli.shutil.which", return_value="/usr/bin/glab"):
        result = runner.invoke(app, ["pr", "--create"], input="y\n")

    glab_calls = [c for c in captured if c and c[0] == "glab"]
    assert len(glab_calls) == 1
    assert glab_calls[0][:3] == ["glab", "mr", "create"]
    assert "--title" in glab_calls[0]
    assert "add login feature" in glab_calls[0]
    assert "https://gitlab.com" in result.output


def test_create_cli_not_installed_exits():
    with patch("gitai.cli.get_branch_name", return_value="feature/login"), \
         patch("gitai.cli.subprocess.run", return_value=MagicMock(returncode=0, stdout="")), \
         patch("gitai.cli.get_base_branch", return_value="main"), \
         patch("gitai.cli.get_commits_since_base", return_value=[{"subject": "s", "diff": "d"}]), \
         patch("gitai.cli.load_config", return_value=_base_config()), \
         patch("gitai.cli.get_repo_name", return_value="myrepo"), \
         patch("gitai.cli.build_pr_prompt", return_value="prompt"), \
         patch("gitai.cli.get_pr_description", return_value=FAKE_DESCRIPTION), \
         patch("gitai.cli.get_remote_provider", return_value="github"), \
         patch("gitai.cli.shutil.which", return_value=None):
        result = runner.invoke(app, ["pr", "--create"], input="y\n")
    assert result.exit_code != 0
    assert "gh" in result.output
    assert "cli.github.com" in result.output


def test_parse_default_format():
    description = """## Title
add user authentication via OAuth

## Description
This PR adds OAuth-based authentication.

### Changes
- add OAuth flow
- add token storage
"""
    title, body = _parse_pr_title_body(description)
    assert title == "add user authentication via OAuth"
    assert "## Description" in body
    assert "## Title" not in body


def test_parse_minimal_format():
    description = """## Title
fix null pointer in login

## Description
- fix null check
- add guard clause
"""
    title, body = _parse_pr_title_body(description)
    assert title == "fix null pointer in login"
    assert "- fix null check" in body


def test_parse_title_stripped():
    description = "## Title\n  padded title  \n\n## Description\nbody"
    title, _ = _parse_pr_title_body(description)
    assert title == "padded title"


def test_parse_missing_title_section():
    title, body = _parse_pr_title_body("## Description\nsome body")
    assert title == ""
    assert "some body" in body
