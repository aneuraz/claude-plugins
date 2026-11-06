---
title: NEVER write a version from memory
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/never-write-a-version-from-memory.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# NEVER write a version from memory

When adding a dependency, let the package manager resolve the latest compatible version and update the lock; never type the version number.

*Justification:* an agent's training data is out of date, and so is a number written by hand. **A plan or a brief does not exempt you from resolving**: versions frozen in a design document are as reliable as memory, that is, not at all. Resolve at implementation time and flag the gap rather than copying.
