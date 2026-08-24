---
name: draft-pr-description
description: Create or revise standardized pull request descriptions for OmniSight. Use when opening, updating, reviewing, or summarizing a PR and when a reproducible SHA-256 identifier, major changes, rationale, risks, evidence, and follow-up work must be documented.
---

# Draft PR Description

Inspect the complete committed diff before writing. Exclude untracked and unrelated local changes.

## Workflow

1. Determine the PR base and head. Prefer PR metadata; otherwise use the default branch and `HEAD`.
2. Read the commits, changed files, diff, linked task, requirements, and relevant ADRs.
3. Run `scripts/pr_digest.py --base <base> --head <head>` from the repository root.
4. Copy `assets/pr-description-template.md`, resolve every placeholder, and remove inapplicable optional sections.
5. Describe outcomes and design intent, not a file-by-file transcription.
6. Report only validation actually executed. State limitations explicitly.
7. Recalculate the digest whenever the committed diff changes.

## Content rules

- Lead with the problem and resulting behavior.
- Group major changes by capability or concern.
- Explain important decisions, constraints, alternatives, and compatibility effects.
- Link ClickUp tasks, requirements, ADRs, issues, and dependent PRs when known.
- Identify security, privacy, accessibility, database, network, deployment, and rollback impact when relevant.
- Distinguish automated accessibility findings from checks requiring human validation.
- Never claim WCAG conformity from automated checks alone.
- Do not claim tests, reviews, approvals, or deployment evidence that was not observed.
- Never include secrets, personal data, raw third-party page content, or machine-local paths.

## Review digest

Use the script output without editing it. The digest is SHA-256 over the exact bytes produced by:

```text
git diff --binary --no-ext-diff <base>...<head>
```

Record the resolved base commit, head commit, algorithm, and digest. This identifies the reviewed
content; it is not a signature, approval, security guarantee, or substitute for the head commit SHA.

## Quality gate

Verify that every placeholder is resolved, the summary matches the diff, breaking changes and
migrations are explicit, validation has evidence, risks have mitigations or owners, the digest is
current, and no unrelated work is attributed to the PR.
