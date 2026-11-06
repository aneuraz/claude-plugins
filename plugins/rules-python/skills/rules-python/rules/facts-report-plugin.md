---
title: facts report plugin
sources:
  - https://github.com/aneuraz/candle/blob/275bce0/.claude/skills/spec-to-facts/references/test-patterns.md
---

# facts report plugin

Each pytest job writes a report of its tests' outcomes. A pytest plugin, loaded from the root `conftest.py` (`pytest_plugins = ("scripts.facts_report",)`), writes `{node_id: outcome}` as JSON when the session ends. The node id is pytest's own (`<file>::<function>` or `<file>::<function>[<case>]`); the outcome is one of `passed`, `skipped`, `failed`, `error`, `xfailed`, `xpassed`.

```python
import json
from pathlib import Path

import pytest

_REPORTS: dict[str, list[pytest.TestReport]] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--facts-report", default=None, metavar="PATH")


def pytest_runtest_logreport(report: pytest.TestReport) -> None:
    _REPORTS.setdefault(report.nodeid, []).append(report)


def _outcome(phases: list[pytest.TestReport]) -> str:
    if any(r.failed and r.when in ("setup", "teardown") for r in phases):
        return "error"
    calls = [r for r in phases if r.when == "call"]
    if any(r.failed for r in calls):
        return "failed"
    if any(r.passed and hasattr(r, "wasxfail") for r in calls):
        return "xpassed"
    if any(r.skipped and hasattr(r, "wasxfail") for r in phases):
        return "xfailed"
    if any(r.skipped for r in phases):
        return "skipped"
    return "passed"


def pytest_sessionfinish(session: pytest.Session) -> None:
    path = session.config.getoption("--facts-report")
    if path is None:
        return
    out = {node: _outcome(phases) for node, phases in _REPORTS.items()}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out), encoding="utf-8")
```

Each test job passes the option through the environment (`PYTEST_ADDOPTS: --facts-report=reports/<job>.json`), so the job's command is unchanged, and uploads `reports/` as an artifact named after the job. The report file's stem is the job name; two reports with the same stem fail the gate.
