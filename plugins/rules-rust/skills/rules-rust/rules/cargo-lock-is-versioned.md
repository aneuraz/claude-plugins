---
title: '`Cargo.lock` MUST be versioned, binaries included'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# `Cargo.lock` MUST be versioned, binaries included

Realises `rules-security:lockfile-versioned-and-authoritative` (ANSSI rule `DENV-CARGO-LOCK`).

*Justification:* the lockfile constrains the checksums of the dependencies; see the security rule for why a single-user binary is no exception.
