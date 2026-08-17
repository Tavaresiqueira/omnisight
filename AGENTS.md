# AGENTS.md

Guidance for coding agents working in this repository. Keep these instructions practical and update them when the same mistake recurs.

## Project context

OmniSight is an accessibility platform for scanning web pages, explaining barriers, tracking improvements and applying reversible local adaptations. Product decisions must consider WCAG 2.2 in Brazilian Portuguese and must distinguish automated findings from checks that require human validation.

Do not assume a framework, cloud service or architectural pattern that is not yet established in the repository. Inspect the existing project before proposing or implementing one.

## Working principles

- Inspect the relevant code path before editing.
- Make the smallest correct change that satisfies the requested behavior.
- Keep every changed line traceable to the request, a failing test or a concrete bug found during implementation.
- Match established repository patterns before introducing a new abstraction.
- Reuse existing models, schemas, validators, services, components and utilities when they fit.
- Keep unrelated cleanup, refactors and optional improvements out of the patch.
- Prefer clear local code over a premature generic helper.
- Preserve user changes and never discard unrelated work from a dirty worktree.

## Scope and abstraction discipline

- Do not add features, configurability or fallback behavior beyond the requested scope.
- Do not create generic helpers, coercion utilities, serializers, wrappers or compatibility layers for hypothetical failures.
- A helper with one call site is justified only when it materially clarifies domain behavior.
- Do not hide failures with broad exception handling. Catch errors only where recovery, translation or cleanup is explicit and useful.
- Avoid duplicating a domain rule across layers; place it at the narrowest established ownership boundary.
- Prefer reversible changes and small reviewable commits.

## Boundaries and validation

Treat the following as untrusted boundaries:

- User-provided URLs and form input.
- External websites and browser content.
- HTTP request and response payloads.
- External APIs, webhooks and third-party integrations.
- File import and export.
- Database ingestion originating outside the validated application flow.
- Messages, cache values or queue payloads written by another service or version.

At a real boundary, validate input explicitly and fail with a clear domain error. Within trusted, typed and already validated internal flows, do not add redundant parsing or defensive coercion.

Before adding a fallback, helper or broad exception handler, answer:

1. What concrete failure can occur?
2. Where can invalid data enter?
3. Why is recovery better than a clear failure?
4. Why are existing project mechanisms insufficient?

If the justification is hypothetical, do not add it.

## Security, privacy and accessibility

- Treat any server-side fetch of a user-provided URL as an SSRF-sensitive operation.
- Apply allow/deny rules, redirect validation, timeouts, resource limits and execution isolation where relevant.
- Minimize collection and retention of page content, personal data and scan artifacts.
- Never claim complete WCAG conformity from automated scanning alone.
- Preserve keyboard navigation, semantic HTML, accessible names, visible focus, contrast and reduced-motion preferences in user interfaces.
- Reference the applicable WCAG 2.2 success criterion when implementing or testing an accessibility rule.
- Keep browser-extension adaptations local, reversible and permission-minimal.

## Planning gate

For ambiguous work, multi-file changes, persistence changes, concurrency, authentication, external integrations or security-sensitive behavior, produce a short plan before implementation covering:

- Files and components to change.
- Existing abstractions to reuse.
- Trust boundaries involved.
- Tests and evidence required.
- Why any new abstraction or fallback is necessary.

Then implement only the agreed or clearly supported scope.

## Verification

- Run the narrowest relevant checks first.
- Add or update focused tests for behavioral changes.
- Strengthen validation for permissions, persistence, concurrency, queues, security boundaries and API contracts.
- For accessible interfaces, test keyboard behavior and the relevant automated accessibility checks; include assistive-technology or manual review when risk warrants it.
- Review the final diff and remove speculative code, unrelated cleanup and unsupported claims.
- State what was validated and what could not be validated.

## Git discipline

- Use concise Conventional Commit messages that describe intent.
- Keep unrelated changes in separate commits.
- Never mention an AI tool, model or agent in branches, commits or generated documentation.
- Do not commit secrets, local credentials, generated caches or temporary artifacts.
