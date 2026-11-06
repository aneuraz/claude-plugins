---
title: An SBOM MUST be produced at each release
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/sbom-at-each-release.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# An SBOM MUST be produced at each release

Produced from the lockfile (`cyclonedx-py` or equivalent from `uv.lock`) and kept with the artefact.

*Justification:* makes it possible to answer "are we exposed to CVE-XXXX" in hours rather than days, which incident management expects.
