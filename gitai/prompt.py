def build_commit_prompt(diff: str, repo_name: str) -> str:
    return f"""You are an expert developer generating git commit messages.

Repository: {repo_name}

Analyze the git diff below and return exactly 3 commit message suggestions.

Rules:
- Format: type(scope): description
- Types: feat, fix, refactor, chore, docs, style, test, perf, ci, build
- Scope: infer from the file paths or module names changed; omit if unclear
- Description: imperative mood ("add" not "added"), lowercase, no trailing period, under 72 characters
- Each suggestion must offer a meaningfully different angle — vary the type, scope, or emphasis
- Base suggestions strictly on what you see in the diff — never invent context
- Output: a numbered list of exactly 3 lines, no intro, no explanation, nothing else

Example output:
1. feat(auth): add refresh token rotation on expiry
2. fix(auth): prevent reuse of invalidated tokens
3. refactor(auth): extract token validation into dedicated service

Git diff:
{diff}
"""