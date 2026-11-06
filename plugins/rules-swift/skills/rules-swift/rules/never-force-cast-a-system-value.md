---
title: 'A value coming from the system MUST NOT be force-cast with `as!`'
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# A value coming from the system MUST NOT be force-cast with `as!`

Use `as?` and handle the failure.

*Justification:* a failing `as!` terminates the process, on a path where an invariant of the specification may forbid failure.
