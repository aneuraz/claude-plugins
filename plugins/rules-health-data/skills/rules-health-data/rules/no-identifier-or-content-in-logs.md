---
title: Logs MUST NOT contain a direct identifier or user content
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-identifier-or-content-in-logs.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#4-no-leakage-of-sensitive-data
---

# Logs MUST NOT contain a direct identifier or user content

A structured logger with a central redaction processor based on a **field allow-list**; never free interpolation of a domain structure. Log the `correlation_id`, never the content.

*Justification:* logs have a life cycle, a replication and access rights distinct from those of the store; they are easily exported outside the authorised perimeter.
