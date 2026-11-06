---
title: The project version is never written by hand
sources:
- https://github.com/aneuraz/candle/blob/275bce0/docs/wiki/rules/version-never-written-by-hand.md
- https://github.com/aneuraz/candle-legacy/blob/0a910516ab7dfdfa461c21190b79c40b126dc876/docs/security-rules.md#1-toolchain-and-dependencies
---

# The project version is never written by hand

Not in `pyproject.toml`, not in a `__version__`, not in a `VERSION` file, not in the documentation.

*Justification:* `pyproject.toml` declares `dynamic = ["version"]` and the version **is** the git tag, computed at build time by `hatch-vcs`. A number written by hand is duplicated data, and all duplicated data diverges; the tag is the only source, set by a human release act. To read the version at runtime: `importlib.metadata.version("<distribution>")`. A PR that touches the version when that is not its sole purpose is to be rejected.
