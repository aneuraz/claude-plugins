---
title: The purge (TTL) MUST be checked by a test
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/purge-checked-by-a-test.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#8-resilience
---

# The purge (TTL) MUST be checked by a test

The test shows that an expired piece of data is no longer accessible or present in the store.

*Justification:* minimal retention is a protection measure (the less data there is, the less a compromise exposes) and a GDPR requirement.
