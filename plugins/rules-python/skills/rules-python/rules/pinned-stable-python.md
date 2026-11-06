---
title: Development MUST use a stable version of Python, pinned in `.python-version`, which is versioned
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/pinned-stable-python.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# Development MUST use a stable version of Python, pinned in `.python-version`, which is versioned

No alpha/beta version. Check the latest stable release of the series (`uv python list`) before pinning; do not default to pinning what is installed.

*Justification:* build reproducibility between developer machine, CI and release, a condition for a usable audit. An outdated toolchain blocks the security tooling downstream.
