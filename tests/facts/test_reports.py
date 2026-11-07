"""`load_reports` reads the pytest format and the normalized one, in one directory."""

import json
from pathlib import Path

import pytest

from claude_plugins_tools.facts.reports import (
    DuplicateReportError,
    Entry,
    MalformedReportError,
    load_reports,
)


def _write(directory: Path, name: str, content: object) -> None:
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(content), encoding="utf-8")


def test_a_pytest_report_becomes_entries(tmp_path: Path) -> None:
    _write(tmp_path, "py.json", {"tests/t.py::a[x]": "passed"})
    entry = load_reports(tmp_path)["py"]["tests/t.py::a[x]"]
    assert entry == Entry("tests/t.py::a[x]", "tests/t.py::a[x]", "passed", "tests/t.py", None)


def test_a_normalized_report_keeps_every_field(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "ui.json",
        {
            "tests/a.test.ts::d > APP-001 x": {
                "title": "APP-001 x",
                "outcome": "failed",
                "file": "tests/a.test.ts",
                "binary": "pkg::bin",
            },
            "bare": {"outcome": "passed"},
        },
    )
    entries = load_reports(tmp_path)["ui"]
    assert entries["tests/a.test.ts::d > APP-001 x"] == Entry(
        "tests/a.test.ts::d > APP-001 x", "APP-001 x", "failed", "tests/a.test.ts", "pkg::bin"
    )
    assert entries["bare"] == Entry("bare", "bare", "passed", None, None)


def test_both_formats_in_one_directory(tmp_path: Path) -> None:
    _write(tmp_path, "a/py.json", {"tests/t.py::a": "passed"})
    _write(tmp_path, "b/ui.json", {"f.ts::T": {"title": "T", "outcome": "passed", "file": "f.ts"}})
    reports = load_reports(tmp_path)
    assert set(reports) == {"py", "ui"}
    assert reports["ui"]["f.ts::T"].file == "f.ts"
    assert reports["py"]["tests/t.py::a"].outcome == "passed"


def test_an_absent_directory_holds_no_report(tmp_path: Path) -> None:
    assert load_reports(tmp_path / "nope") == {}


def test_two_reports_for_one_job_raise(tmp_path: Path) -> None:
    _write(tmp_path, "a/job.json", {})
    _write(tmp_path, "b/job.json", {})
    with pytest.raises(DuplicateReportError):
        load_reports(tmp_path)


@pytest.mark.parametrize("content", [[1], {"k": 3}, {"k": {"title": "t"}}, {"k": {"outcome": 1}}])
def test_a_malformed_report_raises(tmp_path: Path, content: object) -> None:
    _write(tmp_path, "bad.json", content)
    with pytest.raises(MalformedReportError):
        load_reports(tmp_path)


def test_invalid_json_raises(tmp_path: Path) -> None:
    (tmp_path / "bad.json").write_text("{", encoding="utf-8")
    with pytest.raises(MalformedReportError):
        load_reports(tmp_path)
