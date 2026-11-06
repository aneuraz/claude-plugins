---
title: 'The Rust CI gates are formatting, `clippy` with warnings denied, and the tests'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# The Rust CI gates are formatting, `clippy` with warnings denied, and the tests

Realises `rules-security:ci-gates`. No merge without:

```
cargo fmt --all -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --workspace
```

plus the audit gates of `rules-rust:cargo-audit-and-deny-on-every-pr`.
