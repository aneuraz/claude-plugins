---
name: rules-swift
description: 'Swift rules: Package.resolved, checked return codes of system APIs, no forced casts of system values, and swift test in CI. Cited as rules-swift:<slug>. Read a rule file when a skill or the base rules cite it, or before writing Swift or changing its dependencies.'
paths:
- '**/*.swift'
- Package.swift
---

# Swift rules

Rule files sit in `rules/`, one per file. Cite one as `rules-swift:<slug>`.

## Rules

- `Package.resolved` MUST be versioned — `rules-swift:package-resolved-is-versioned`
- The return code of a C system API MUST be checked — `rules-swift:check-system-api-return-codes`
- A value coming from the system MUST NOT be force-cast with `as!` — `rules-swift:never-force-cast-a-system-value`
- `swift test` MUST be a CI gate — `rules-swift:swift-test-in-ci`
