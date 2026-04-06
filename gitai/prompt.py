def build_commit_prompt(diff: str, repo_name: str, emoji: bool = False, commit_style: str = "conventional", num_suggestions: int = 3) -> str:
    format_rules = _build_format_rules(commit_style, emoji)
    example = _build_example(commit_style, emoji)

    return f"""You are an expert developer generating git commit messages.

Repository: {repo_name}

Analyze the git diff below and return exactly {num_suggestions} commit message suggestions.

Rules:
{format_rules}
- Each suggestion must offer a meaningfully different angle — vary the type, scope, or emphasis
- Base suggestions strictly on what you see in the diff — never invent context
- Output: a numbered list of exactly {num_suggestions} lines, no intro, no explanation, nothing else

Example output:
{example}

Git diff:
{diff}
"""


def _build_format_rules(commit_style: str, emoji: bool) -> str:
    if commit_style == "free-form":
        rules = (
            "- Format: a single clear imperative sentence, no type prefix required\n"
            "- Keep the message under 72 characters\n"
            '- Imperative mood ("add" not "added"), lowercase, no trailing period'
        )
        if emoji:
            rules += "\n- Prefix each message with a relevant emoji that reflects the nature of the change"
    else:  # conventional (default)
        rules = (
            "- Format: type(scope): description\n"
            "- Types: feat, fix, refactor, chore, docs, style, test, perf, ci, build\n"
            "- Scope: infer from the file paths or module names changed; omit if unclear\n"
            '- Description: imperative mood ("add" not "added"), lowercase, no trailing period, under 72 characters'
        )
        if emoji:
            rules += (
                "\n- Prefix each message with the matching gitmoji before the type: "
                "✨ feat, 🐛 fix, ♻️ refactor, 🔧 chore, 📝 docs, 🎨 style, ✅ test, ⚡ perf, 👷 ci, 📦 build"
            )
    return rules


def _build_example(commit_style: str, emoji: bool) -> str:
    if commit_style == "free-form":
        if emoji:
            return (
                "1. ✨ add refresh token rotation on session expiry\n"
                "2. 🐛 prevent reuse of invalidated tokens\n"
                "3. ♻️ extract token validation into dedicated service"
            )
        return (
            "1. add refresh token rotation on session expiry\n"
            "2. prevent reuse of invalidated tokens\n"
            "3. extract token validation into dedicated service"
        )
    else:  # conventional
        if emoji:
            return (
                "1. ✨ feat(auth): add refresh token rotation on expiry\n"
                "2. 🐛 fix(auth): prevent reuse of invalidated tokens\n"
                "3. ♻️ refactor(auth): extract token validation into dedicated service"
            )
        return (
            "1. feat(auth): add refresh token rotation on expiry\n"
            "2. fix(auth): prevent reuse of invalidated tokens\n"
            "3. refactor(auth): extract token validation into dedicated service"
        )
