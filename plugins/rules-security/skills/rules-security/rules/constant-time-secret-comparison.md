---
title: Secret comparisons MUST be constant-time
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/constant-time-secret-comparison.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
---

# Secret comparisons MUST be constant-time

Secret comparisons MUST be constant-time (in Python, `secrets.compare_digest`), and generating randomness for security MUST use a cryptographic source (in Python, the `secrets` module): never `random`, never a timestamp as a seed.
