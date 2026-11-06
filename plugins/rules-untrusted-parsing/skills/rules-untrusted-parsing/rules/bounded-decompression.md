---
title: Decompression MUST be bounded
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/bounded-decompression.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
---

# Decompression MUST be bounded

Maximum decompressed size, maximum number of entries, refusal of traversing paths (`..` segments) in archives.

*Justification:* a decompression bomb is a DoS; an archive entry with a traversing path is an arbitrary write.
