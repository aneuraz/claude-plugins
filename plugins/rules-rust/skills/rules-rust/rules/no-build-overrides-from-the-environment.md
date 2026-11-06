---
title: '`RUSTC`, `RUSTC_WRAPPER` and `RUSTFLAGS` MUST NOT be set when calling cargo, and the development checks MUST stay on'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# `RUSTC`, `RUSTC_WRAPPER` and `RUSTFLAGS` MUST NOT be set when calling cargo, and the development checks MUST stay on

Realises `rules-security:runtime-defined-by-the-repository` for the build. `debug-assertions` and `overflow-checks` MUST NOT be disabled in `[profile.dev]` or `[profile.test]`.

*Justification:* (ANSSI) options scattered in the environment make the build unauditable, and disabling these checks hides the bugs the development profile exists to reveal.
