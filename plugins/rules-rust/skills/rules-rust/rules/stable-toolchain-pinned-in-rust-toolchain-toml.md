---
title: 'Development MUST use the `stable` toolchain, pinned in a versioned `rust-toolchain.toml`'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# Development MUST use the `stable` toolchain, pinned in a versioned `rust-toolchain.toml`

Realises `rules-security:runtime-defined-by-the-repository` and `rules-security:deal-with-outdated-dependencies` for the toolchain.

No unstable feature and no `rustup override` to `nightly`; if a tool requires it, run `cargo +nightly <command>` once. Check the pinned version is current (`rustup check`) instead of copying whatever is installed.

*Justification:* the build is the same on the workstation and in CI. A stale toolchain blocks `cargo-audit` and `cargo-deny` in cascade.
