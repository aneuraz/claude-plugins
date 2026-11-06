---
title: Outdated dependencies MUST be dealt with before each development cycle
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/deal-with-outdated-dependencies.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# Outdated dependencies MUST be dealt with before each development cycle

Before each development cycle, list the outdated dependencies (with uv: `uv lock --upgrade --dry-run` or `uv tree --outdated`) and deal with each: an update, or keeping the version with a written justification.

*Justification:* a dependency frozen without justification becomes security debt (ANSSI MCO/MCS pillar: maintaining security condition).
