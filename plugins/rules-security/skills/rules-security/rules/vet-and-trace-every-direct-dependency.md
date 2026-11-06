---
title: Every direct dependency MUST be vetted and the vetting traced
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/vet-and-trace-every-direct-dependency.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# Every direct dependency MUST be vetted and the vetting traced

Transitive dependencies SHOULD be.

*Justification:* supply chain control (ANSSI governance pillar). Expected trace: name, version, one-line reason for adding it, maintainer, licence, review date. An untraced dependency is a merge refusal. Prefer the standard library. A package with no release for more than 18 months is a warning sign: flag it, do not add it silently. Take particular care with the ML ecosystem: a model is downloaded from an identified source, with a pinned revision.
