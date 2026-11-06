---
title: 'Lifting `forbid(unsafe_code)` MUST be an explicit decision taken outside the agent, confined to a dedicated module'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# Lifting `forbid(unsafe_code)` MUST be an explicit decision taken outside the agent, confined to a dedicated module

Every `unsafe` block in that module carries a `// SAFETY:` comment stating why it is sound.

*Justification:* `unsafe` that is not isolated makes auditing the whole crate necessary; isolated, it makes the audit proportionate.
