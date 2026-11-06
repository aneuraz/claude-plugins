---
title: '`Package.resolved` MUST be versioned'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# `Package.resolved` MUST be versioned

Realises `rules-security:lockfile-versioned-and-authoritative` for SwiftPM.

*Justification:* it pins the dependency revisions; see the security rule. Prefer the system frameworks to a package where they do the job: a project with no dependency has nothing to trace under `rules-security:vet-and-trace-every-direct-dependency`.
