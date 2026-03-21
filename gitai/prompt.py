def build_commit_prompt(diff: str, repo_name: str) -> str:
    return f"""You are an expert developer helping generate git commit messages.

Analyze this git diff from the repository "{repo_name}" and suggest 3 commit messages.

Rules:
- Use Conventional Commits format: type(scope): description
- Types: feat, fix, chore, refactor, docs, style, test
- Keep messages under 72 characters
- Be specific and descriptive, not generic
- Base suggestions ONLY on what you see in the diff, never invent context
- If the diff is minimal, keep suggestions simple and honest
- Return ONLY a numbered list with 3 options, nothing else

Example output:
1. feat(auth): add JWT refresh token support
2. feat(auth): implement token expiration handling
3. refactor(auth): extract token logic into service

Git diff:
{diff}
"""