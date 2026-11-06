---
title: Validation MUST happen at the edge, once, and produce a validated type
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/validate-once-at-the-edge.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# Validation MUST happen at the edge, once, and produce a validated type

The input models validate; the core of the code handles types that are already safe (`NewType`, frozen models) and does not validate again.

*Justification:* the absence of validation deep in the code becomes impossible by construction, not by discipline. A core that validates again is a core whose boundary is in the wrong place.
