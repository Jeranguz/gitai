from unittest.mock import patch, MagicMock
from gitai.git import is_diff_meaningful, get_staged_diff, get_repo_name

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
