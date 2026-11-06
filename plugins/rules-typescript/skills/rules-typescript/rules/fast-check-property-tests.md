---
title: fast-check property tests
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# fast-check property tests

A level 2 fact (a predicate over a whole input domain) is a fast-check property.

```ts
fc.assert(fc.property(fc.array(fc.integer()), (xs) => {
  const out = dedupe(xs);
  return new Set(out).size === out.length;         // invariant: uniqueness
}));
```
