---
title: The service MUST restart safely
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/restart-safely.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#8-resilience
---

# The service MUST restart safely

At startup, a job interrupted by a shutdown is resumed or marked as failed, never left in a phantom "in progress" state, never silently replayed twice.
