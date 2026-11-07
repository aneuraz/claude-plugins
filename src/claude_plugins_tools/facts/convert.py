"""Converters from each runner's raw report to the normalized report format.

`cpt facts report vitest|playwright|nextest <raw> <out>` writes
``{"<id>": {"title": ..., "outcome": ..., "file": ..., "binary": ...}}``, which
`reports.load_reports` reads; ``file`` and ``binary`` appear when the runner has
them. Outcomes are ``passed``, ``failed`` or ``skipped``; a flaky test is
``failed`` (it did not hold every time); two entries under one id keep the worse
outcome, so neither hides the other. An outcome a map does not know passes
through and ranks worst.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET  # noqa: S405 — nextest's own report, written by the CI job
from pathlib import Path, PurePosixPath

VITEST_OUTCOMES = {
    "passed": "passed",
    "failed": "failed",
    "skipped": "skipped",
    "pending": "skipped",
    "todo": "skipped",
}
PLAYWRIGHT_OUTCOMES = {
    "expected": "passed",
    "unexpected": "failed",
    "flaky": "failed",
    "skipped": "skipped",
}
RANK = {"passed": 0, "skipped": 1, "failed": 2}
# Children of a nextest <testcase>: a failure, an error, or a retry that failed first.
NEXTEST_FAILED = ("failure", "error", "flakyFailure", "flakyError", "rerunFailure", "rerunError")

type Entries = dict[str, dict[str, str]]


class ConvertError(Exception):
    """A raw report the converter cannot read: an empty output would hide its tests."""


def _record(entries: Entries, key: str, outcome: str, **fields: str) -> None:
    held = entries.get(key)
    if held is None or RANK.get(outcome, len(RANK)) > RANK.get(held["outcome"], len(RANK)):
        entries[key] = {**fields, "outcome": outcome}


def _repo_relative(name: str, root: str, repo: Path) -> str:
    """The repository-relative file of a vitest `name`.

    vitest ran in `<repo>/<root>`. An absolute name (vitest's own form) must lie
    under that directory; a relative one is taken as relative to it. Either way
    the file is `<root>/<path within root>`, so a name outside `root` is refused
    rather than guessed.
    """
    base = repo.resolve() / root
    path = Path(name)
    if path.is_absolute():
        path = path.resolve()  # the base is resolved: a symlinked checkout must not break it
        try:
            within = path.relative_to(base)
        except ValueError:
            raise ConvertError(f"{name} is outside {base} (--root {root!r})") from None
    else:
        within = path
    return (PurePosixPath(root) / within.as_posix()).as_posix()


def from_vitest(raw: dict, root: str, repo: Path) -> Entries:
    """vitest's JSON reporter; `root` is the directory vitest ran in, relative to
    the repository at `repo`."""
    entries: Entries = {}
    for file in raw["testResults"]:
        relative = _repo_relative(file["name"], root, repo)
        for test in file["assertionResults"]:
            full = " > ".join([*test["ancestorTitles"], test["title"]])
            outcome = VITEST_OUTCOMES.get(test["status"], test["status"])
            _record(entries, f"{relative}::{full}", outcome, title=test["title"], file=relative)
    return entries


def from_playwright(raw: dict, test_dir: str) -> Entries:
    """Playwright's JSON reporter: top suites are files, the suites under them
    describes. A spec's file is relative to the configured test directory, so
    `test_dir` (relative to the repository) is prefixed."""
    entries: Entries = {}

    def walk(suite: dict, describes: list[str]) -> None:
        for spec in suite.get("specs", []):
            full = " > ".join([*describes, spec["title"]])
            file = (PurePosixPath(test_dir) / spec["file"]).as_posix() if test_dir else spec["file"]
            # One test per project the spec ran in.
            for test in spec["tests"]:
                outcome = PLAYWRIGHT_OUTCOMES.get(test["status"], test["status"])
                _record(entries, f"{file}::{full}", outcome, title=spec["title"], file=file)
        for child in suite.get("suites", []):
            walk(child, [*describes, child["title"]])

    for file_suite in raw["suites"]:
        walk(file_suite, [])
    return entries


def from_nextest(text: str) -> Entries:
    """cargo-nextest's JUnit XML. A `<testsuite>` is a test binary, named
    `<package>` for a `--lib` binary and `<package>::<bin>` for an integration
    test; the id is `<binary>::<test path>`. Ignored tests are not entries."""
    entries: Entries = {}
    for suite in ET.fromstring(text).iter("testsuite"):  # noqa: S314
        binary = suite.get("name", "")
        for case in suite.iter("testcase"):
            if case.find("skipped") is not None:
                continue
            failed = any(case.find(tag) is not None for tag in NEXTEST_FAILED)
            name = case.get("name", "")
            _record(
                entries,
                f"{binary}::{name}",
                "failed" if failed else "passed",
                title=name,
                binary=binary,
            )
    return entries


def convert(  # noqa: PLR0913 — one knob per runner option
    runner: str,
    raw: Path,
    out: Path,
    *,
    root: str = "",
    test_dir: str = "",
    repo: Path | None = None,
) -> Path:
    """Write the normalized report of `raw` to `out`; raises ConvertError when
    `raw` is not the runner's report."""
    try:
        text = raw.read_text(encoding="utf-8")
        if runner == "nextest":
            entries = from_nextest(text)
        else:
            data = json.loads(text)
            if runner == "vitest":
                entries = from_vitest(data, root.strip("/"), repo or Path.cwd())
            else:
                entries = from_playwright(data, test_dir.strip("/"))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, ET.ParseError) as error:
        raise ConvertError(f"{raw}: not a {runner} report ({error!r})") from error
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(entries, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """The `report` group's options, on `parser`."""
    parser.add_argument("runner", choices=("vitest", "playwright", "nextest"))
    parser.add_argument("raw", type=Path, help="the runner's raw report")
    parser.add_argument("out", type=Path, help="the normalized report to write")
    parser.add_argument(
        "--root",
        default="",
        metavar="DIR",
        help="vitest: the directory vitest ran in, relative to the repository "
        "(absolute names must lie under it)",
    )
    parser.add_argument(
        "--test-dir",
        default="",
        metavar="DIR",
        help="playwright: the configured test directory, relative to the repository",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        metavar="DIR",
        help="vitest: the repository root (default: the current directory)",
    )
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        convert(
            args.runner, args.raw, args.out, root=args.root, test_dir=args.test_dir, repo=args.repo
        )
    except ConvertError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1
    return 0
