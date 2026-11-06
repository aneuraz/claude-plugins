---
title: The return code of a C system API MUST be checked
sources:
- https://github.com/aneuraz/capture/blob/300a95f/SECURITY.md
---

# The return code of a C system API MUST be checked

This covers the status of Carbon and Core Foundation calls (`OSStatus`) and of the Accessibility API (`AXError`), such as `RegisterEventHotKey` and `AXUIElementCopyAttributeValue`.

*Justification:* an ignored return code gives a program that starts, reports success and silently never does its job (a hotkey that never fires).
