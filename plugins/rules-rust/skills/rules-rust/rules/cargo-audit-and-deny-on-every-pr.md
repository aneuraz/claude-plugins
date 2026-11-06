---
title: '`cargo audit` and `cargo deny check` MUST run in CI on every PR'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# `cargo audit` and `cargo deny check` MUST run in CI on every PR

Realises the dependency audit of `rules-security:ci-gates`.

*Justification:* `cargo audit` searches the RustSec Advisory Database for known vulnerabilities; `cargo deny check` also checks licences and sources.
