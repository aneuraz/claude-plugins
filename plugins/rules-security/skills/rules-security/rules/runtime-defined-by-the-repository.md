---
title: The runtime environment MUST be entirely defined by the repository
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/runtime-defined-by-the-repository.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# The runtime environment MUST be entirely defined by the repository

No undocumented environment variable needed at startup, and no search path patched from outside the packaging. Everything goes through packaging (the package manager's run command, declared entry points).

*Justification:* a scattered environment makes the build and the incident impossible to audit.
