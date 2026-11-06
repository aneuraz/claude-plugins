---
title: Image rendering MUST be bounded
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/bounded-image-rendering.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#2-dynamic-code-and-parsing-of-untrusted-content
---

# Image rendering MUST be bounded

An explicit pixel limit, never disabled (with Pillow, `Image.MAX_IMAGE_PIXELS`), a capped rendering resolution, a capped number of pages.

*Justification:* a 40,000 × 40,000 pixel image in a one-megabyte PDF exhausts the service's memory.
