---
title: Authorisation MUST be checked on every access to a piece of data, at the level of the data, not of the route
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/authorise-at-the-data-not-the-route.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#6-authentication-authorisation-traceability
---

# Authorisation MUST be checked on every access to a piece of data, at the level of the data, not of the route

The storage layer performs the ownership check on every read and every deletion, not the route.

*Justification:* checking per route lets horizontal access through: a legitimate caller reading another caller's data. It is the most frequent class of vulnerability on this kind of service.
