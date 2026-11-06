---
title: '`uv.lock` MUST be versioned and authoritative'
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/uv-lock-is-authoritative.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# `uv.lock` MUST be versioned and authoritative

`uv` is the only manager: no manual `pip install`, no parallel `requirements.txt`.

*Justification:* the lockfile freezes versions and hashes. A mismatch between the downloaded sources and the lock produces an error, and that is the detection we want. Without a versioned lock, every build starts over on TOFU (*trust on first use*) and a dependency substitution goes unnoticed.
