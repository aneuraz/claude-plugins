---
name: rules-rust
description: 'Rust rules: the pinned stable toolchain, Cargo.lock, cargo audit and deny, cargo outdated, no build overrides, forbid(unsafe_code) and its exceptions, and the CI gates. Cited as rules-rust:<slug>. Read a rule file when a skill or the base rules cite it, or before writing Rust or changing its dependencies.'
paths:
- '**/*.rs'
- Cargo.toml
- Cargo.lock
---

# Rust rules

Rule files sit in `rules/`, one per file. Cite one as `rules-rust:<slug>`.

## Rules

- Development MUST use the `stable` toolchain, pinned in a versioned `rust-toolchain.toml` — `rules-rust:stable-toolchain-pinned-in-rust-toolchain-toml`
- `Cargo.lock` MUST be versioned, binaries included — `rules-rust:cargo-lock-is-versioned`
- A dependency''s trace MUST record whether it contains `unsafe`, and the standard library comes first — `rules-rust:dependency-trace-records-unsafe-and-prefers-std`
- `cargo audit` and `cargo deny check` MUST run in CI on every PR — `rules-rust:cargo-audit-and-deny-on-every-pr`
- `cargo outdated` MUST be run before each development cycle — `rules-rust:cargo-outdated-before-each-cycle`
- `RUSTC`, `RUSTC_WRAPPER` and `RUSTFLAGS` MUST NOT be set when calling cargo, and the development checks MUST stay on — `rules-rust:no-build-overrides-from-the-environment`
- Every crate MUST carry `#![forbid(unsafe_code)]` at its root — `rules-rust:forbid-unsafe-code-in-every-crate`
- Lifting `forbid(unsafe_code)` MUST be an explicit decision taken outside the agent, confined to a dedicated module — `rules-rust:lifting-the-unsafe-ban-is-a-decision`
- The Rust CI gates are formatting, `clippy` with warnings denied, and the tests — `rules-rust:rust-ci-gates`
