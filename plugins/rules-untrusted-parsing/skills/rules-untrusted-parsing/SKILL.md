---
name: rules-untrusted-parsing
description: 'Rules for code that parses files or streams supplied by third parties: bounded decompression of archives, bounded image and PDF rendering, a file''s type from its magic bytes. Cited as rules-untrusted-parsing:<slug>. Read a rule file when a skill or the base rules cite it, or before parsing an uploaded file.'
---

# Untrusted-parsing rules

Rule files sit in `rules/`, one per file. Cite one as `rules-untrusted-parsing:<slug>`.

- Decompression MUST be bounded — `rules-untrusted-parsing:bounded-decompression`
- Image rendering MUST be bounded — `rules-untrusted-parsing:bounded-image-rendering`
- A file's type MUST be established from its content (magic bytes), never from its extension or its declared Content-Type — `rules-untrusted-parsing:file-type-from-magic-bytes`
