"""Test reports and the judgement of a check against them.

A report is one JSON file per CI job, in either of two formats, which a directory
may mix:

* pytest's: ``{"<node id>": "<outcome>"}``, written by the ``report`` plugin;
* the normalized one: ``{"<id>": {"title": ..., "outcome": ..., "file": ..., "binary": ...}}``,
  where ``title`` defaults to the id and ``file`` and ``binary`` are present when
  the runner has them.

Both load as ``Entry`` values keyed by job, then id. A check selects entries; a fact
is green when each part of its check selects at least one entry and every selected
entry passed. No report, or no selected entry, reads ``not run``, never green.
"""

import json
import re
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import NamedTuple

from claude_plugins_tools.facts import cargo
from claude_plugins_tools.facts.selectors import (
    SELECTOR_PATTERN,
    by_id_selector,
    runner_of,
    split_parts,
)

NOT_RUN = "not run"
SKIPPED = "skipped"
FAILED = "failed"
XFAIL = "xfail"
REASONS = {
    "skipped": SKIPPED,
    "failed": FAILED,
    "error": FAILED,
    "xfailed": XFAIL,
    "xpassed": XFAIL,
}


class Entry(NamedTuple):
    """One test's outcome, whatever runner wrote it."""

    id: str
    title: str
    outcome: str
    file: str | None = None
    binary: str | None = None


type Reports = dict[str, dict[str, Entry]]


class DuplicateReportError(Exception):
    """Two report files name one job: keeping either would hide the other."""

    def __init__(self, job: str) -> None:
        super().__init__(job)
        self.job = job


class MalformedReportError(Exception):
    """A report file that is neither format: reading it as empty would hide its tests."""

    def __init__(self, path: Path, why: str) -> None:
        super().__init__(f"{path}: {why}")
        self.path = path
        self.why = why


class RedTest(NamedTuple):
    test: str
    reason: str
    job: str


def _entry(path: Path, key: str, value: object) -> Entry:
    if isinstance(value, str):  # pytest's format: the node id is the key
        return Entry(key, key, value, key.partition("::")[0])
    if isinstance(value, dict) and isinstance(value.get("outcome"), str):
        fields = {"title": key, "file": None, "binary": None} | value
        title, file, binary = fields["title"], fields["file"], fields["binary"]
        if isinstance(title, str) and all(x is None or isinstance(x, str) for x in (file, binary)):
            return Entry(key, title, value["outcome"], file, binary)
    raise MalformedReportError(path, f"{key!r} is neither a pytest outcome nor a normalized entry")


def load_reports(directory: Path) -> Reports:
    """Every report under `directory`, keyed by its job (the file's stem);
    an absent directory holds none. A job reported twice raises
    DuplicateReportError: the second must not silently replace a red first."""
    reports: Reports = {}
    if not directory.is_dir():
        return reports
    for path in sorted(directory.rglob("*.json")):
        if path.stem in reports:
            raise DuplicateReportError(path.stem)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError) as error:
            raise MalformedReportError(path, f"not readable JSON: {error}") from error
        if not isinstance(raw, dict):
            raise MalformedReportError(path, "not a JSON object")
        reports[path.stem] = {key: _entry(path, key, value) for key, value in raw.items()}
    return reports


def _covers(selector: re.Match[str], node_id: str) -> bool:
    """A selector naming a case stands for that case alone; one naming a
    function stands for the function and each of its cases."""
    if selector.group(3):
        return node_id == selector.group(0)
    base = f"{selector.group(1)}::{selector.group(2)}"
    return node_id == base or node_id.startswith(f"{base}[")


def _red(entry: Entry, job: str) -> RedTest | None:
    if entry.outcome == "passed":
        return None
    return RedTest(entry.id, REASONS.get(entry.outcome, f"unknown outcome {entry.outcome}"), job)


def red_tests(
    check: str,
    reports: Reports,
    runner_forms: Mapping[str, tuple[str, ...]] | None = None,
    release_reports: Collection[str] = (),
) -> list[RedTest]:
    """Each test this check names that the reports do not show passed; a part that
    selects nothing yields one `not run`. The parts joined by `&&` all count: the fact
    is green when every part selects at least one entry and every selected entry passed."""
    red: list[RedTest] = []
    for part in split_parts(check):
        red += _part_red(part, reports, runner_forms, release_reports)
    return red


def _cargo_red(part: str, reports: Reports, release_reports: Collection[str]) -> list[RedTest]:
    parsed = cargo.parse(part)
    if isinstance(parsed, str):
        return [RedTest(part, NOT_RUN, "")]
    # The profile decides which reports are read: a release check never reads a debug
    # report, nor the other way round.
    jobs = {
        job: [(e.id, e.title) for e in report.values() if e.binary == parsed.binary]
        for job, report in reports.items()
        if (job in release_reports) == parsed.release
    }
    red: list[RedTest] = []
    for filter_, selected in cargo.select(parsed, jobs):
        if not selected:
            what = f"{parsed.binary} {filter_}" if filter_ else parsed.binary
            red.append(RedTest(what, NOT_RUN, ""))
        for job, entry_id, _ in selected:
            if (item := _red(reports[job][entry_id], job)) is not None:
                red.append(item)
    return red


def _part_red(
    check: str,
    reports: Reports,
    runner_forms: Mapping[str, tuple[str, ...]] | None,
    release_reports: Collection[str],
) -> list[RedTest]:
    runner = runner_of(check)
    if runner == "cargo":
        return _cargo_red(check, reports, release_reports)
    if runner == "swift":
        return []  # audited for form only; no report holds it
    by_id = by_id_selector(check, runner_forms)
    if by_id is not None:
        file, fact_id = by_id
        # The test's own title, never the describe path in the id: a describe
        # named after an id would otherwise stand for its tests.
        selected = [
            (job, entry)
            for job, report in reports.items()
            for entry in report.values()
            if entry.file == file and entry.title.startswith(f"{fact_id} ")
        ]
        if not selected:
            return [RedTest(f"{file} {fact_id}", NOT_RUN, "")]
        return [red for job, entry in selected if (red := _red(entry, job)) is not None]
    matches = list(SELECTOR_PATTERN.finditer(check)) if runner_of(check) == "pytest" else []
    if not matches:
        return [RedTest(check, NOT_RUN, "")]
    red: list[RedTest] = []
    for match in matches:
        seen = False
        for job, report in reports.items():
            for entry in report.values():
                if not _covers(match, entry.id):
                    continue
                seen = True
                if (item := _red(entry, job)) is not None:
                    red.append(item)
        if not seen:
            red.append(RedTest(match.group(0), NOT_RUN, ""))
    return red
