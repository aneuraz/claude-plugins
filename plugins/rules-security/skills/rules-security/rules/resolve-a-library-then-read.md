---
title: Before using a library you do not know well, resolve it, then read
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/resolve-a-library-then-read.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# Before using a library you do not know well, resolve it, then read

Read the resolved version first (with uv: `uv pip show <package>`), then the documentation for **that version**.

*Justification:* an error after adding a dependency is solved with the CHANGELOG of the exact version, not by guessing the signature.
