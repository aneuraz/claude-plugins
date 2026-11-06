---
title: '`uv.lock` MUST be versioned and authoritative'
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/uv-lock-is-authoritative.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# `uv.lock` MUST be versioned and authoritative

The Python realisation of `rules-security:lockfile-versioned-and-authoritative`, which holds the justification. `uv` is the only manager: commit `uv.lock`, install from it (`uv sync --locked`), no manual `pip install`, no parallel `requirements.txt`.
