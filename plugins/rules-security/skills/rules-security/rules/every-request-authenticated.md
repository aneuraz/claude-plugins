---
title: Every request MUST be authenticated
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/every-request-authenticated.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#6-authentication-authorisation-traceability
---

# Every request MUST be authenticated

The chosen mechanism (hashed API key, OIDC token validated locally, mTLS) is a recorded decision of the project. When several mechanisms coexist, the shape of the presented credential routes a request to one of them unambiguously, never by trial and error, which pays the verification cost twice.
