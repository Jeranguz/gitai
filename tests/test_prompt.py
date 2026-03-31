from gitai.prompt import build_commit_prompt, _build_format_rules, _build_example

SAMPLE_DIFF = "diff --git a/foo.py b/foo.py\n+def bar(): pass"


# --- _build_format_rules ---

def test_conventional_no_emoji_has_type_format():
    rules = _build_format_rules("conventional", False)
    assert "type(scope): description" in rules
    assert "feat, fix" in rules

def test_conventional_no_emoji_has_no_gitmoji():
    rules = _build_format_rules("conventional", False)
    assert "✨" not in rules

def test_conventional_with_emoji_includes_gitmoji_map():
    rules = _build_format_rules("conventional", True)
    assert "✨ feat" in rules
    assert "🐛 fix" in rules
    assert "♻️ refactor" in rules

def test_freeform_no_emoji_omits_type_prefix():
    rules = _build_format_rules("free-form", False)
    assert "type(scope)" not in rules
    assert "imperative mood" in rules.lower()

def test_freeform_with_emoji_includes_emoji_instruction():
    rules = _build_format_rules("free-form", True)
    assert "emoji" in rules.lower()

def test_freeform_with_emoji_omits_gitmoji_type_map():
    # free-form emoji rule is generic, not a type→emoji map
    rules = _build_format_rules("free-form", True)
    assert "✨ feat" not in rules


# --- _build_example ---

def test_conventional_example_uses_type_scope_format():
    example = _build_example("conventional", False)
    assert "feat(" in example
    assert "fix(" in example
    assert "refactor(" in example

def test_conventional_example_is_numbered():
    example = _build_example("conventional", False)
    assert example.startswith("1.")

def test_conventional_emoji_example_has_gitmoji():
    example = _build_example("conventional", True)
    assert "✨" in example
    assert "🐛" in example

def test_freeform_example_has_no_type_scope():
    example = _build_example("free-form", False)
    assert "feat(" not in example
    assert "fix(" not in example

def test_freeform_emoji_example_has_emoji():
    example = _build_example("free-form", True)
    assert "✨" in example


# --- build_commit_prompt ---

def test_prompt_contains_diff():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert SAMPLE_DIFF in prompt

def test_prompt_contains_repo_name():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert "myrepo" in prompt

def test_prompt_conventional_by_default():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert "type(scope)" in prompt

def test_prompt_freeform_style_omits_type_scope():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo", commit_style="free-form")
    assert "type(scope)" not in prompt

def test_prompt_emoji_enabled_includes_gitmoji():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo", emoji=True)
    assert "✨" in prompt

def test_prompt_emoji_disabled_by_default():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert "✨" not in prompt

def test_prompt_requests_exactly_3_suggestions():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert "3" in prompt

def test_prompt_instructs_no_extra_output():
    prompt = build_commit_prompt(SAMPLE_DIFF, "myrepo")
    assert "nothing else" in prompt
