---
title: A ruff warning gets fixed, not ignored
sources:
- https://github.com/aneuraz/candle/blob/275bce0/CLAUDE.md#4-completion-gate
---

# A ruff warning gets fixed, not ignored

`# noqa` / `# type: ignore` only on the offending line, with the precise error code and a comment giving the reason. Any automatic fix (`ruff --fix`) gets reread before commit: the tool does not guarantee that semantics are preserved.
