---
title: facts report plugin
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# facts report plugin

Each pytest job writes a report of its tests' outcomes. The plugin ships in the tooling package: the root `conftest.py` loads it with `pytest_plugins = ("claude_plugins_tools.facts.report",)`, and with `--facts-report PATH` it writes `{node_id: outcome}` as JSON when the session ends. The node id is pytest's own (`<file>::<function>` or `<file>::<function>[<case>]`); the outcome is one of `passed`, `skipped`, `failed`, `error`, `xfailed`, `xpassed`. A failed setup or teardown is `error` even when the call also failed; then a failed call is `failed`; then the xfail and skip cases.

Each test job passes the option through the environment (`PYTEST_ADDOPTS: --facts-report=reports/<job>.json`), so the job's command is unchanged, and uploads `reports/` as an artifact named after the job. The report file's stem is the job name; two reports with the same stem fail the gate. A test that spawns pytest without the plugin strips `PYTEST_ADDOPTS` from the child's environment.
