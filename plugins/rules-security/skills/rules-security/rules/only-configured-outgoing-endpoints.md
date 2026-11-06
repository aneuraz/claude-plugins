---
title: Outgoing calls MUST target only explicitly configured endpoints
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/only-configured-outgoing-endpoints.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
---

# Outgoing calls MUST target only explicitly configured endpoints

No URL derived from user input; the list of authorised hosts is the configuration itself.

*Justification:* shuts SSRF through configuration, and makes the data's destinations auditable: "what data leaves, and to where" is the first question asked in an audit.
