---
title: '`swift test` MUST be a CI gate'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# `swift test` MUST be a CI gate

Realises `rules-security:ci-gates` for Swift code: no merge without `swift test` (with `--package-path` when the package is not at the root), alongside the language-neutral gates.
