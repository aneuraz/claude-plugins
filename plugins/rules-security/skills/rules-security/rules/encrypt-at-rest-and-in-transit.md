---
title: Sensitive data MUST be encrypted at rest and in transit, including on internal links
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/encrypt-at-rest-and-in-transit.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
---

# Sensitive data MUST be encrypted at rest and in transit, including on internal links

An encrypted storage volume (a documented deployment requirement), TLS between components or documented strict co-location, TTL + automatic purge. Any queue or cache added later inherits the same requirement.

*Justification:* encryption between components limits the reach of a compromise of a single component (independence of layers: the threat model in this pack's skeleton).

How a project meets the rule (which links rely on co-location, which proxy variables each client reads, where its store's encrypted volume is) is the project's own page, citing this rule.
