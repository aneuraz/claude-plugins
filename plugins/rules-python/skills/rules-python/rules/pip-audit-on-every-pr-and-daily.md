---
title: '`pip-audit` MUST run in CI on every PR and on a daily cron'
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/pip-audit-on-every-pr-and-daily.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# `pip-audit` MUST run in CI on every PR and on a daily cron

CI audits `uv.lock`, not an environment: an audit run against an environment audits whatever that environment holds, the audit tool's own included, not the project's locked dependencies.

*Justification:* search for known vulnerabilities (OSV/PyPI Advisory databases). A critical advisory on a production dependency blocks the deployment.
