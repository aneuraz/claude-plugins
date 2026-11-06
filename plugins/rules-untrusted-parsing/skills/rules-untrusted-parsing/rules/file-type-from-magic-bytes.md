---
title: A file's type MUST be established from its content (magic bytes), never from its extension or its declared Content-Type
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/file-type-from-magic-bytes.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# A file's type MUST be established from its content (magic bytes), never from its extension or its declared Content-Type

*Justification:* the extension is a statement by the attacker; dispatching to a parser on that basis runs the wrong hardened code on the wrong content.
