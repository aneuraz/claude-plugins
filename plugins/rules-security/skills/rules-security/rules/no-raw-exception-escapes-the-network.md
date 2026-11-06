---
title: A code path reachable from the network MUST NOT let a raw exception escape
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-raw-exception-escapes-the-network.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# A code path reachable from the network MUST NOT let a raw exception escape

A global handler turns everything into an opaque error + correlation_id (`rules-security:opaque-error-responses`); validation never relies on a construct the runtime can strip; access to a key or an index of incoming data checks its presence explicitly.

*Justification:* an unhandled exception in a handler is a denial of service and a leak channel (stack trace). It is a security incident, not an ergonomics defect.
