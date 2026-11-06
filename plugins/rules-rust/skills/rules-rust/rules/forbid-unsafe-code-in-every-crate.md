---
title: 'Every crate MUST carry `#![forbid(unsafe_code)]` at its root'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# Every crate MUST carry `#![forbid(unsafe_code)]` at its root

*Justification:* the value of Rust here is its memory guarantees. An `unsafe` block suspends them and puts the code back at the level of C, with the burden of proof on the author.
