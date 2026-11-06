---
title: '`eval`, `exec`, `pickle`/`shelve` on external data, and non-safe `yaml.load` ARE FORBIDDEN'
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/no-eval-exec-pickle-or-unsafe-yaml.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
---

# `eval`, `exec`, `pickle`/`shelve` on external data, and non-safe `yaml.load` ARE FORBIDDEN

Use `yaml.safe_load`, `json`/`orjson`, and serialisation formats that do not execute code.

*Justification:* executable deserialisation is arbitrary code execution handed to the attacker. Watch out for ML model loading: no pickle checkpoint of unverified origin (`safetensors` or a pinned revision from a trusted source).
