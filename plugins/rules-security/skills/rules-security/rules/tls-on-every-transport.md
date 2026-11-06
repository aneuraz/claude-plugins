---
title: TLS MUST be required on every transport
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/tls-on-every-transport.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#5-transport-storage-cryptography
---

# TLS MUST be required on every transport

TLS is verified on outgoing calls too (no `verify=False`, ever).

*Justification:* a debugging `verify=False` that reaches production cancels the trust perimeter.
