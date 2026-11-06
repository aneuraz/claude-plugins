---
title: Access logs MUST NOT be modifiable by the service that produces them
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/access-logs-unmodifiable-by-producer.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#6-authentication-authorisation-traceability
---

# Access logs MUST NOT be modifiable by the service that produces them

*Justification:* a log the compromised component can alter has no evidential value.
