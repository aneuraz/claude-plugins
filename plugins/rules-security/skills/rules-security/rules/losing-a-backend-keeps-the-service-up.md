---
title: Losing a backend MUST NOT bring the service down
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/losing-a-backend-keeps-the-service-up.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#8-resilience
---

# Losing a backend MUST NOT bring the service down

The job concerned fails cleanly, readiness degrades, the other backends carry on.
