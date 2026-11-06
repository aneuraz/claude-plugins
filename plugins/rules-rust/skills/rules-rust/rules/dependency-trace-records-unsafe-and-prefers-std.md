---
title: 'A dependency''s trace MUST record whether it contains `unsafe`, and the standard library comes first'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# A dependency's trace MUST record whether it contains `unsafe`, and the standard library comes first

Realises `rules-security:vet-and-trace-every-direct-dependency` for crates: next to name, version, reason, maintainer, licence and review date, the trace says whether the crate contains `unsafe`. A crate with no release for more than 18 months is flagged and a decision recorded. Before adding a crate, check whether the pinned toolchain's `std` now covers the need (for example `File::try_lock` and `File::unlock` instead of a file-lock crate); if not, prefer the maintained fork over the abandoned crate.

*Justification:* `unsafe` in a dependency suspends the memory guarantees the language gives (`rules-rust:forbid-unsafe-code-in-every-crate`); the trace is where that is seen.
