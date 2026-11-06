---
title: Input schemas MUST refuse unknown fields
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/input-schemas-refuse-unknown-fields.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# Input schemas MUST refuse unknown fields

An input schema rejects a payload that carries a field it does not declare, rather than ignoring the field.

*Justification:* an unknown field accepted silently masks an integration error or an attempt to get around validation.
