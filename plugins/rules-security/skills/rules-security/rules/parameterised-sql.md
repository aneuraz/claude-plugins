---
title: Every SQL query MUST be parameterised
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/parameterised-sql.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# Every SQL query MUST be parameterised

Concatenation is forbidden, including for a column name: in that case, use an allow-list.
