---
title: Every access to sensitive data MUST be logged
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/log-every-sensitive-access.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#6-authentication-authorisation-traceability
---

# Every access to sensitive data MUST be logged

Who (the full identity, never a fragment), what, when, from where. These access logs MUST be a stream separate from the application logs, write-only, with a fixed retention period.

*Justification:* enforceable traceability (ANSSI defence pillar: collecting the events that make detection possible).
