---
title: CI gates
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/ci-gates.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#7-ci-gates
---

# CI gates

The CI is authoritative. At minimum it runs formatting, lint, type checking, the import contract where the project declares one, each test suite, and the dependency audit; on a release tag, the release workflow adds the SBOMs (`rules-security:sbom-at-each-release`), a reproducible build from the lockfile and the image scan.

**A test MUST check the no-leak guarantees mechanically** (the "No leakage of sensitive data" section of this pack's skeleton): submitting synthetic content leaves no trace of that content in the captured logs or in the error responses.

*Justification:* a rule nothing checks mechanically is not a rule. The agent and the developer alike can bypass it through inattention.
