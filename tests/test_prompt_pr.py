from gitai.prompt import build_pr_prompt

FAKE_COMMITS = [
    {"subject": "feat(auth): add login endpoint", "diff": "+def login(): pass"},
    {"subject": "fix(auth): handle expired tokens", "diff": "+if expired: raise"},
]

FAKE_TEMPLATE = "## Summary\n{summary}\n\n## Checklist\n- [ ] tests"


# --- default mode ---

def test_default_mode_includes_repo_name():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="default")
    assert "myrepo" in prompt

def test_default_mode_includes_commit_subjects():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="default")
    assert "feat(auth): add login endpoint" in prompt
    assert "fix(auth): handle expired tokens" in prompt

def test_default_mode_includes_commit_diffs():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="default")
    assert "+def login(): pass" in prompt

def test_default_mode_requests_summary_and_testing_sections():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="default")
    assert "summary" in prompt.lower() or "testing" in prompt.lower()


# --- minimal mode ---

def test_minimal_mode_includes_repo_name():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="minimal")
    assert "myrepo" in prompt

def test_minimal_mode_requests_bullet_list():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="minimal")
    assert "bullet" in prompt.lower() or "- [" in prompt or "list" in prompt.lower()

def test_minimal_mode_does_not_mention_testing_notes():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", mode="minimal")
    assert "testing notes" not in prompt.lower()


# --- template mode ---

def test_template_mode_includes_template_content():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", template=FAKE_TEMPLATE)
    assert "## Summary" in prompt
    assert "## Checklist" in prompt

def test_template_mode_includes_commit_context():
    prompt = build_pr_prompt(FAKE_COMMITS, "", "myrepo", template=FAKE_TEMPLATE)
    assert "feat(auth): add login endpoint" in prompt


# --- full-diff mode (diff provided, commits empty) ---

def test_full_diff_mode_includes_diff():
    prompt = build_pr_prompt([], "+flat diff content", "myrepo", mode="default")
    assert "+flat diff content" in prompt

def test_full_diff_mode_with_empty_commits_does_not_crash():
    prompt = build_pr_prompt([], "+flat diff content", "myrepo", mode="default")
    assert isinstance(prompt, str)
    assert len(prompt) > 0
