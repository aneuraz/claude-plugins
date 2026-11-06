---
title: Secrets MUST be handled through dedicated types
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/secrets-through-dedicated-types.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#4-no-leakage-of-sensitive-data
---

# Secrets MUST be handled through dedicated types

Secrets are held in a dedicated type that neutralises accidental display, **and injected by the environment or a vault.** No secret in the code, the tests, the fixtures, the versioned config or the git history. An exposed secret is deemed compromised and MUST be revoked, not removed from the history.

*Justification:* a dedicated type neutralises accidental display; rotation is the only effective remedy for exposure.
