---
title: TypeScript rules
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/typescript-rules.md
---

# TypeScript rules

The style is Biome and ultracite (`biome.jsonc`), and `pnpm check` has the last word. These rules only record what you need to know before the tool tells you.

## The gate

Run locally what the CI job runs, for example:

```
pnpm check && pnpm exec tsc --noEmit && pnpm test:unit
```

A Biome warning gets fixed. A Biome suppression stays local, names the rule and says why. Reread what `pnpm fix` changed before committing: the tool does not guarantee that the meaning survives.

## Dependencies

Add a dependency with `pnpm add`, never by writing a version by hand: `rules-security:never-write-a-version-from-memory`.

## What Biome rejects, and what to write instead

- An `if` without braces. Every `if` has its own.
- `forEach`. Write a `for … of` loop.
- The non-null assertion `!`. Test the value and handle its absence.
- `import * as`. Import the names you use.
- An `async` function without `await` (`useAwait`). Write `() => Promise.resolve(x)`.
- A constructor parameter that declares a field (`noParameterProperties`). Declare the field explicitly.
- An `export` in a test file (`noExportsInTest`). A helper shared between tests lives in its own module.

## Code blocks in a plan

A block marked "add" puts its `import` statements at the top of the target file, with the others.
