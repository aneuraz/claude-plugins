"""Pytest plugin: record each test's outcome, by node id, for the facts gate.

With ``--facts-report PATH`` it writes ``{node_id: outcome}`` as JSON when the session
ends. The outcome is read from the test's phases and the first match wins, in this
order on purpose: a failed setup or teardown is ``error`` even when the call also
failed (both are red), then a failed call is ``failed``, then the xfail and skip cases.
Every call report counts: the ``subtests`` fixture logs one per subtest under the
parent's node id.

In CI the option travels in ``PYTEST_ADDOPTS``, so a test that spawns pytest without
this plugin must strip that variable from the child's environment.
"""

import json
from pathlib import Path
from typing import Final

import pytest

OUTCOMES: Final = ("passed", "skipped", "failed", "error", "xfailed", "xpassed")

_REPORTS: Final[dict[str, list[pytest.TestReport]]] = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--facts-report",
        default=None,
        metavar="PATH",
        help="write each test's outcome, by node id, as JSON to PATH",
    )


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
    outcomes = {nodeid: _outcome(phases) for nodeid, phases in _REPORTS.items()}
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(outcomes, indent=2) + "\n", encoding="utf-8")
