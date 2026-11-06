---
title: A type that carries sensitive data MUST NOT have a default representation
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-default-repr-for-sensitive-types.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#4-no-leakage-of-sensitive-data
---

# A type that carries sensitive data MUST NOT have a default representation

A common base whose representation (in Python, `__repr__`/`__str__`) redacts the fields concerned; no `print()` and no f-string of a domain object in shipped code. Never a dataclass or a `BaseModel` with the default repr on a type that carries identifying data.

*Justification:* this is the most frequent and the least visible way data leaks. A default repr combined with a `logger.error("%s", job)` in a rare error path exports the record into the logs, often to an aggregator, sometimes outside the authorised perimeter.
