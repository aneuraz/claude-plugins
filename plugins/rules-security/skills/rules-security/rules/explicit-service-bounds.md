---
title: The service MUST enforce explicit bounds
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/explicit-service-bounds.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# The service MUST enforce explicit bounds

Maximum size of request body and of file, maximum number of pages, read/write timeouts, rate limiting per caller.

*Justification:* without explicit bounds, a processing service is a DoS amplifier: a few requests are enough to saturate memory and compute.
