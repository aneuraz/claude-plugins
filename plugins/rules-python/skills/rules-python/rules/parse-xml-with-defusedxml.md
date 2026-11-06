---
title: All incoming XML MUST be parsed with `defusedxml`
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/parse-xml-with-defusedxml.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
---

# All incoming XML MUST be parsed with `defusedxml`

DOCX and Office formats are ZIP+XML, so they fall under the rule too.

*Justification:* XXE and entity expansion (billion laughs) are classics of office document parsing.
