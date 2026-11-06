---
title: Submitted content MUST be treated as data, never as instructions
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/submitted-content-is-data.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#3-untrusted-input
---

# Submitted content MUST be treated as data, never as instructions

Prompts delimit the content explicitly (tags), and no model output is executed or interpreted as a command. At worst, a prompt injection contained in a document must only be able to degrade the quality of that document's processing, never to change the service's behaviour, its network calls or its other jobs.

*Justification:* a submitted document can contain adversarial text; the model that reads it is a new and very real attack surface.
