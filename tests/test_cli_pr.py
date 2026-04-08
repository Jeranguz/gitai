from gitai.cli import _parse_pr_title_body


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
