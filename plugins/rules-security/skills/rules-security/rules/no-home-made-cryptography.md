---
title: The project MUST NOT implement any cryptographic primitive
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-home-made-cryptography.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
---

# The project MUST NOT implement any cryptographic primitive

Use an audited library (in Python, `cryptography`, and `hashlib` for digests). Hash secrets with a dedicated function (argon2/scrypt through an audited library) or salted HMAC-SHA-256, never a bare SHA-256 on a low-entropy secret.

*Justification:* crypto implementation errors cannot be detected by functional tests.
