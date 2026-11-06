---
name: rules-typescript
description: 'TypeScript rules: the Biome style and what it rejects, the pnpm gate, pnpm add, and the Jest and fast-check side of spec-to-facts. Cited as rules-typescript:<slug>. Read a rule file when a skill or the base rules cite it, or before writing TypeScript.'
paths:
- '**/*.ts'
- '**/*.tsx'
- package.json
---

# TypeScript rules

Rule files sit in `rules/`, one per file. Cite one as `rules-typescript:<slug>`.

## Rules

- TypeScript rules — `rules-typescript:typescript-rules`

## The test side of spec-to-facts

- Jest example tests — `rules-typescript:jest-example-tests`
- fast-check property tests — `rules-typescript:fast-check-property-tests`
