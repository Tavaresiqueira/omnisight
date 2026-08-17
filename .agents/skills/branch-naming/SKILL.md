---
name: branch-naming
description: Create, rename, or select concise Git branch names that follow repository conventions. Use when starting work on a branch, preparing a worktree, or correcting an unclear or tool-branded branch name.
---

# Branch Naming

1. Inspect the current branch and nearby branch names.
2. Derive the name from the user-facing change, not the AI tool or developer.
3. Use lowercase kebab-case.
4. Preserve prefixes such as `feature/`, `fix/`, or `hotfix/` only when the repository uses them.
5. Keep the name short while retaining the differentiating business concept.
6. Never include `copilot`, `codex`, `openai`, model names, or agent names.
7. Verify the result with `git branch --show-current`.

Examples: `fix/incorrect-expiry-alert`, `client-option-opportunity-monitor`, `add-quote-comparison`.
