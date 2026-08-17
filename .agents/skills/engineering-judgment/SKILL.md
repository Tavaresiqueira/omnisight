---
name: engineering-judgment
description: Apply proportional engineering effort, scope control, and risk-based validation. Use for implementation planning, test decisions, debugging strategy, delegation, or deciding how much change a task justifies.
---

# Engineering Judgment

1. Inspect the existing path before editing.
2. Make the smallest correct change satisfying the requested behavior.
3. Reuse existing models, validators, serializers, services, and conventions before adding abstractions.
4. Keep unrelated cleanup out of the patch.
5. Treat user input, external APIs, files, databases, shared queues, and cross-service caches as boundaries.
6. Do not add fallback parsing, coercion, broad exception handling, or generic helpers for hypothetical failures.
7. Scale validation to risk:
   - Inspection or syntax checks for cosmetic and mechanical work.
   - Focused tests for behavioral changes.
   - Stronger tests for financial calculations, permissions, persistence, concurrency, integrations, and API contracts.
8. Review the final diff and remove speculative code.
9. State what was validated and what could not be validated.
