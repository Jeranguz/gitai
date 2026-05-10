import pytest
from unittest.mock import patch, MagicMock
from gitai.git import (
    is_diff_meaningful, get_staged_diff, get_repo_name, truncate_diff,
    get_branch_name, get_base_branch, get_commits_since_base, get_diff_since_base,
    get_remote_provider,
)

MEANINGFUL_DIFF = """\
diff --git a/foo.py b/foo.py
index abc..def 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@
 def foo():
+    return 42
-    pass
"""


def _mock_run(stdout):
    """Helper to create a mock subprocess.run result."""
    return MagicMock(stdout=stdout, returncode=0)


# --- is_diff_meaningful ---

def test_meaningful_diff_returns_true():
    assert is_diff_meaningful(MEANINGFUL_DIFF) is True

def test_empty_string_returns_false():
    assert is_diff_meaningful("") is False

def test_only_header_lines_returns_false():
    diff = "--- a/foo.py\n+++ b/foo.py\n"
    assert is_diff_meaningful(diff) is False

def test_blank_added_line_returns_false():
    diff = "--- a/foo.py\n+++ b/foo.py\n+\n"
    assert is_diff_meaningful(diff) is False

def test_blank_removed_line_returns_false():
    diff = "--- a/foo.py\n+++ b/foo.py\n-\n"
    assert is_diff_meaningful(diff) is False

def test_single_added_line_returns_true():
    diff = "+def new_function(): pass"
    assert is_diff_meaningful(diff) is True

def test_single_removed_line_returns_true():
    diff = "-old_code = True"
    assert is_diff_meaningful(diff) is True

def test_only_whitespace_change_returns_false():
    diff = "+   \n-  \n"
    assert is_diff_meaningful(diff) is False


# --- get_staged_diff ---

def test_get_staged_diff_returns_stdout():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="diff --git a/foo.py b/foo.py\n+change")
        result = get_staged_diff()
    assert result == "diff --git a/foo.py b/foo.py\n+change"

def test_get_staged_diff_calls_correct_command():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        get_staged_diff()
    mock_run.assert_called_once_with(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

def test_get_staged_diff_returns_empty_string_when_nothing_staged():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        result = get_staged_diff()
    assert result == ""


# --- get_repo_name ---

def test_get_repo_name_returns_string():
    assert isinstance(get_repo_name(), str)

def test_get_repo_name_returns_non_empty():
    assert len(get_repo_name()) > 0


# --- truncate_diff ---

def test_truncate_diff_short_diff_unchanged():
    diff = "a" * 100
    result, was_truncated = truncate_diff(diff, max_chars=200)
    assert result == diff
    assert was_truncated is False

def test_truncate_diff_exact_limit_unchanged():
    diff = "a" * 200
    result, was_truncated = truncate_diff(diff, max_chars=200)
    assert result == diff
    assert was_truncated is False

def test_truncate_diff_long_diff_is_truncated():
    diff = "a" * 300
    result, was_truncated = truncate_diff(diff, max_chars=200)
    assert len(result) == 200
    assert was_truncated is True

def test_truncate_diff_preserves_content_up_to_limit():
    diff = "abcdef"
    result, _ = truncate_diff(diff, max_chars=3)
    assert result == "abc"


# --- get_branch_name ---

def test_get_branch_name_returns_string():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="feature/my-branch\n")
        result = get_branch_name()
    assert result == "feature/my-branch"

def test_get_branch_name_calls_correct_command():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="main\n")
        get_branch_name()
    mock_run.assert_called_once_with(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True, text=True, encoding="utf-8",
    )


# --- get_base_branch ---

def test_get_base_branch_returns_explicit_when_provided():
    result = get_base_branch("development")
    assert result == "development"

def test_get_base_branch_auto_detects_main():
    def fake_run(cmd, **kwargs):
        branch = cmd[-1]
        return MagicMock(returncode=0 if branch == "main" else 1)
    with patch("gitai.git.subprocess.run", side_effect=fake_run):
        result = get_base_branch(None)
    assert result == "main"

def test_get_base_branch_falls_back_to_master():
    def fake_run(cmd, **kwargs):
        branch = cmd[-1]
        return MagicMock(returncode=0 if branch == "master" else 1)
    with patch("gitai.git.subprocess.run", side_effect=fake_run):
        result = get_base_branch(None)
    assert result == "master"

def test_get_base_branch_falls_back_to_develop():
    def fake_run(cmd, **kwargs):
        branch = cmd[-1]
        return MagicMock(returncode=0 if branch == "develop" else 1)
    with patch("gitai.git.subprocess.run", side_effect=fake_run):
        result = get_base_branch(None)
    assert result == "develop"

def test_get_base_branch_exits_when_none_found():
    with patch("gitai.git.subprocess.run", return_value=MagicMock(returncode=1)):
        with pytest.raises(SystemExit):
            get_base_branch(None)


# --- get_commits_since_base ---

def test_get_commits_since_base_returns_list_of_dicts():
    def fake_run(cmd, **kwargs):
        if "log" in cmd:
            return MagicMock(stdout="abc123 feat: add thing\n")
        return MagicMock(stdout="+code change\n")
    with patch("gitai.git.subprocess.run", side_effect=fake_run):
        result = get_commits_since_base("main")
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["subject"] == "feat: add thing"
    assert "+code change" in result[0]["diff"]

def test_get_commits_since_base_returns_empty_for_no_commits():
    with patch("gitai.git.subprocess.run", return_value=MagicMock(stdout="")):
        result = get_commits_since_base("main")
    assert result == []


# --- get_diff_since_base ---

def test_get_diff_since_base_returns_diff_string():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="+some change\n")
        result = get_diff_since_base("main")
    assert result == "+some change\n"

def test_get_diff_since_base_calls_correct_command():
    with patch("gitai.git.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="")
        get_diff_since_base("main")
    mock_run.assert_called_once_with(
        ["git", "diff", "origin/main...HEAD"],
        capture_output=True, text=True, encoding="utf-8",
    )


# --- get_remote_provider ---

def test_get_remote_provider_github():
    with patch("gitai.git.subprocess.run", return_value=_mock_run("https://github.com/user/repo.git\n")):
        assert get_remote_provider() == "github"


def test_get_remote_provider_gitlab():
    with patch("gitai.git.subprocess.run", return_value=_mock_run("https://gitlab.com/user/repo.git\n")):
        assert get_remote_provider() == "gitlab"


def test_get_remote_provider_ssh_github():
    with patch("gitai.git.subprocess.run", return_value=_mock_run("git@github.com:user/repo.git\n")):
        assert get_remote_provider() == "github"


def test_get_remote_provider_ssh_gitlab():
    with patch("gitai.git.subprocess.run", return_value=_mock_run("git@gitlab.com:user/repo.git\n")):
        assert get_remote_provider() == "gitlab"


def test_get_remote_provider_unknown_exits():
    with patch("gitai.git.subprocess.run", return_value=_mock_run("https://bitbucket.org/user/repo.git\n")):
        with pytest.raises(SystemExit) as exc:
            get_remote_provider()
        assert "github.com and gitlab.com" in str(exc.value)


def test_get_remote_provider_no_origin_exits():
    m = MagicMock()
    m.returncode = 128
    m.stdout = ""
    with patch("gitai.git.subprocess.run", return_value=m):
        with pytest.raises(SystemExit) as exc:
            get_remote_provider()
        assert "origin" in str(exc.value)
