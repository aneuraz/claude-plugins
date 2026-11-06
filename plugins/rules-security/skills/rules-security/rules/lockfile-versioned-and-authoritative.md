---
title: The lockfile MUST be versioned and authoritative
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# The lockfile MUST be versioned and authoritative

Commit the lockfile of the project's package manager, for a single-user binary as much as for a service, and install from it: no parallel list of dependencies, no resolution outside it.

*Justification:* the lockfile pins the checksums of the dependencies. Without it every build starts over on TOFU (*trust on first use*) and a dependency substitution goes unnoticed; with it, a mismatch between what is downloaded and what is locked is an error, which is the detection wanted. Language realisations: `rules-python:uv-lock-is-authoritative`, `rules-rust:cargo-lock-is-versioned`, `rules-swift:package-resolved-is-versioned`.
