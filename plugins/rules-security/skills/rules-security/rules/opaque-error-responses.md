---
title: Error responses returned to the caller MUST be opaque
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/opaque-error-responses.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#4-no-leakage-of-sensitive-data
---

# Error responses returned to the caller MUST be opaque

A stable error code + a correlation_id. The detail (technical message, offending value, path) stays on the server side, tied to the same identifier.

*Justification:* detailed error messages are a reconnaissance tool, and a leak channel when the error quotes the rejected value.
