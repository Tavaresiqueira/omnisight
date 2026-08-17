---
name: commit-style
description: Write clear Conventional Commit messages from the staged diff or completed change. Use when preparing, amending, or suggesting a Git commit message.
---

# Commit Style

Inspect the diff before writing the message.

- Use an established type such as `feat`, `fix`, `refactor`, `test`, `docs`, or `chore`.
- Add a concise scope only when useful.
- Describe behavioral intent, not filenames.
- Use imperative mood.
- Add a body for motivation, tradeoffs, migration requirements, or non-obvious effects.
- Never mention the AI tool.
- Do not claim validation unsupported by evidence.

Example:

```text
fix(alerts): prioritize executable unwind value

Rank option opportunities using tradable prices so client-contact alerts reflect
realizable economics.
```
