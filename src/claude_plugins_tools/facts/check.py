"""facts check — exit 0 iff every non-@draft fact passes, no fact is orphaned
and every check names exactly one test.

A fact is orphaned when its id appears in no design document: the fact-set
would then drift from the spec without anything failing. --orphans runs the
traceability check alone, without executing any test.

Selector ambiguity is checked in every mode, for every status, because running
a check cannot reveal it: a selector matching no test exits 0, and a selector
matching two definitions of one name runs the second and reports green.

--implemented runs only the checks of @implemented facts. That is the gate at a
milestone boundary: a @spec fact of a later milestone names a test nobody has
written yet, so running it proves nothing, while an @implemented fact whose
check fails is a claim the repository no longer honours.

A @superseded fact is never run: it names, in superseded_by, the @implemented
fact or facts that bind in its place.

--reports DIR is CI's gate: it runs no check, and holds a fact green
when every test its check names passed in the test jobs' reports under DIR.
Without it, each check runs verbatim, one process each: the local mode.

--exclude-requires LIST (local mode only) lists, without running them, the facts
whose `requires` names a listed resource; a silent exclusion would read as a
pass. Given, it also audits that each fact's `-m` markers equal its `requires`.

--root DIR is the project root (default: the current directory); fact-sets are
read from DIR/docs/superpowers/specs and every selector resolves under DIR.

`[facts] check_forms` in DIR/.claude/project.toml lists the forms a pytest check
may take; absent, no check's form is audited (its selectors still are). The optional
sub-table `[facts.check_forms]` declares per-runner forms (`vitest`, `playwright`, ...);
a vitest or Playwright check in a declared by-id form is judged from the reports'
entries of its file whose own title starts with the fact's id (see selectors.py).
"""

import argparse
import re
import shlex
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

import yaml

from claude_plugins_tools.facts import cargo
from claude_plugins_tools.facts.reports import (
    DuplicateReportError,
    MalformedReportError,
    Reports,
    load_reports,
    red_tests,
)
from claude_plugins_tools.facts.selectors import (
    DEFAULT_VITEST_ROOT,
    RUNNERS,
    runner_of,
    selector_fault,
    split_parts,
)
from claude_plugins_tools.project import ProjectError, load_project

SPEC_SUBDIR = Path("docs") / "superpowers" / "specs"
RANGE_PATTERN = re.compile(r"([A-Z]{2,4})-(\d{3}) (?:à|to) \1-(\d{3})")
MARKER_PATTERN = re.compile(r"(?:^|\s)-m\s+(\w+)")
# The bare gate stays local: Playwright needs an end-to-end stack (services,
# a built front end, browsers), so it runs only when named explicitly.
LOCAL_RUNNERS = ("pytest", "vitest", "cargo")


class Verdict(NamedTuple):
    """What auditing one fact found; each field is None when nothing was."""

    orphan: str | None = None
    ambiguous: str | None = None
    failed: str | None = None
    not_run: str | None = None


def expand_ranges(text: str) -> str:
    """Make "VER-001 à VER-005" match each id it stands for."""
    for match in RANGE_PATTERN.finditer(text):
        prefix, start, end = match.group(1), int(match.group(2)), int(match.group(3))
        text += " " + " ".join(f"{prefix}-{i:03d}" for i in range(start, end + 1))
    return text


def supersession_fault(fact: Mapping[str, object], known: dict[str, str]) -> str | None:
    """A superseded fact stops binding only because others bind in its place:
    each of them must exist and be green."""
    if fact["status"] != "@superseded":
        return None
    named = fact.get("superseded_by")
    successors = (
        [named] if isinstance(named, str) else list(named) if isinstance(named, list) else []
    )
    if not successors:
        return f"{fact['id']} has no superseded_by"
    for successor in map(str, successors):
        if successor not in known:
            return f"{fact['id']} is superseded by {successor}, which does not exist"
        if known[successor] != "@implemented":
            return f"{fact['id']} is superseded by {successor}, which is {known[successor]}"
    return None


def _runner_list(value: str) -> set[str]:
    """argparse type for --runner: a comma list, each name in RUNNERS."""
    names = value.split(",")
    unknown = [name for name in names if name not in RUNNERS]
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown runner(s) {', '.join(unknown)!r}; choose from {', '.join(RUNNERS)}"
        )
    return set(names)


def requires_fault(fact: Mapping[str, object]) -> str | None:
    """A fact's markers must equal its requirements: a check that forgets its
    marker is deselected by addopts, and one that selects a marker its fact does
    not declare escapes --exclude-requires."""
    declared = fact.get("requires", [])
    required = set(declared) if isinstance(declared, list) else set()
    selected = set(MARKER_PATTERN.findall(str(fact["check"])))
    if required != selected:
        return f"requires {sorted(required)} but the check selects {sorted(selected)}"
    return None


def run_check(check: str, root: Path) -> bool:
    """Run one fact's check from `root`, its `&&`-joined parts one after the other
    and stopping at the first failure (no shell involved); on failure, print the
    runner's own output."""
    for part in split_parts(check):
        result = subprocess.run(  # noqa: S603 — argv from the versioned fact-set, no shell
            shlex.split(part), shell=False, capture_output=True, check=False, cwd=root
        )
        if result.returncode != 0:
            for stream in (result.stdout, result.stderr):
                print(stream.decode("utf-8", errors="replace"), end="")
            return False
    return True


def _process_fact(  # noqa: PLR0911, PLR0913 — one return per skip rule, one knob per option
    fact: dict[str, object],
    spec: str,
    args: argparse.Namespace,
    selected: set[str],
    reports: Reports | None = None,
    *,
    root: Path,
    vitest_root: str = DEFAULT_VITEST_ROOT,
    excluded: frozenset[str] = frozenset(),
    forms: Sequence[str] | None = None,
    runner_forms: Mapping[str, tuple[str, ...]] | None = None,
    release_reports: Sequence[str] = (),
    members: cargo.Members | None = None,
) -> Verdict:
    """Audit one fact, then judge it: from `reports` when given, else by
    running its check if selected. `excluded` (local mode only) lists, without
    running, a fact whose `requires` names one of its resources."""
    orphan = fact["id"] if fact["id"] not in spec else None
    # Its test may be gone: the successor carries the guarantee now.
    if fact["status"] == "@superseded":
        return Verdict(orphan)
    ambiguous = None
    # Audited in every mode, --orphans included: running the check cannot
    # reveal the fault, so skipping it in the cheap mode would leave the trap
    # armed exactly where it is cheapest to spot. A @draft fact is exempt:
    # its test is not written yet by definition.
    if fact["status"] != "@draft":
        faults = [
            selector_fault(
                fact["check"],
                root,
                vitest_root,
                forms,
                runner_forms=runner_forms,
                fact_id=str(fact["id"]),
                members=members,
            )
        ]
        if excluded and reports is None:
            faults.append(requires_fault(fact))
        fault = next((fault for fault in faults if fault is not None), None)
        if fault is not None:
            ambiguous = f"{fact['id']} ({fault})"
    if args.orphans or fact["status"] == "@draft":
        return Verdict(orphan, ambiguous)
    if args.implemented and fact["status"] != "@implemented":
        return Verdict(orphan, ambiguous)
    parts = split_parts(fact["check"])
    if reports is not None and all(runner_of(part) == "swift" for part in parts):
        # Audited for form above; no report holds a swift test, so it is not judged.
        print(f"- {fact['id']} [{fact['status']}] not gated (swift): {fact['statement']}")
        return Verdict(orphan, ambiguous)
    if reports is not None:
        red = red_tests(fact["check"], reports, runner_forms, release_reports)
        print(f"{'✗' if red else '✓'} {fact['id']} [{fact['status']}] {fact['statement']}")
        for test in red:
            print(f"    {test.test}: {test.reason}" + (f" ({test.job})" if test.job else ""))
        return Verdict(orphan, ambiguous, fact["id"] if red else None)
    if not {runner_of(part) for part in parts} <= selected:
        return Verdict(orphan, ambiguous)
    required = fact.get("requires", [])
    if isinstance(required, list) and excluded & set(required):
        entry = f"{fact['id']} (requires: {', '.join(sorted(map(str, required)))})"
        return Verdict(orphan, ambiguous, None, entry)
    # A check is a simple command, never a shell line: splitting it rather
    # than interpreting it closes the surface at no cost. A compound check
    # (pipe, redirection) fails here, visibly, which is the right moment to
    # decide whether it belongs in a fact.
    passed = run_check(fact["check"], root)
    print(f"{'✓' if passed else '✗'} {fact['id']} [{fact['status']}] {fact['statement']}")
    return Verdict(orphan, ambiguous, None if passed else fact["id"])


def _reports_of(directory: Path | None) -> Reports | None:
    """The reports under --reports, or None without it; none found is said
    once, and every fact then reads not run."""
    if directory is None:
        return None
    reports = load_reports(directory)
    if not reports:
        print(f"✗ no report under {directory}")
    return reports


def _members_of(root: Path, provider: cargo.Members | None) -> cargo.Members:
    """The workspace members, asked of `cargo metadata` once and only when a cargo
    check needs them; `provider` replaces it (tests)."""
    found: dict[str, Path] | None = None

    def members() -> dict[str, Path]:
        nonlocal found
        if found is None:
            found = dict(provider()) if provider else cargo.workspace_members(root)
        return found

    return members


def build_parser(parser: argparse.ArgumentParser | None = None) -> argparse.ArgumentParser:
    """The facts options, on `parser` when a subcommand supplies one."""
    parser = parser or argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--orphans", action="store_true", help="traceability only")
    parser.add_argument(
        "--implemented",
        action="store_true",
        help="run only the checks of @implemented facts",
    )
    parser.add_argument(
        "--runner",
        default=",".join(LOCAL_RUNNERS),
        type=_runner_list,
        help="comma list of runners to execute (default: pytest,vitest — no e2e stack)",
    )
    parser.add_argument(
        "--reports",
        type=Path,
        metavar="DIR",
        help="judge each fact from the test jobs' reports under DIR; run no check",
    )
    parser.add_argument(
        "--exclude-requires",
        default="",
        metavar="LIST",
        help="local run only: comma list of resources whose facts are listed, not run",
    )
    parser.add_argument(
        "--root", type=Path, default=Path(), metavar="DIR", help="project root (default: .)"
    )
    parser.add_argument(
        "--vitest-root",
        default=DEFAULT_VITEST_ROOT,
        metavar="DIR",
        help="where vitest/Playwright selectors resolve, relative to --root (default: agent)",
    )
    return parser


def run(  # noqa: PLR0912 — one pass, one branch per audit
    args: argparse.Namespace, members: cargo.Members | None = None
) -> int:
    """The gate for parsed `args`; the exit code. `members` replaces `cargo metadata`."""
    selected = args.runner
    root = args.root.resolve()
    excluded = frozenset(name for name in args.exclude_requires.split(",") if name)
    try:
        project = load_project(root)
    except ProjectError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1
    forms, runner_forms = project.check_forms, project.runner_forms
    members = _members_of(root, members)
    try:
        reports = _reports_of(args.reports)
    except DuplicateReportError as error:
        print(f"✗ two reports for job {error.job}")
        return 1
    except MalformedReportError as error:
        print(f"✗ unreadable report: {error}")
        return 1

    failed: list[str] = []
    orphans: list[str] = []
    ambiguous: list[str] = []
    not_run: list[str] = []

    fact_sets = {
        facts_file: yaml.safe_load(facts_file.read_text(encoding="utf-8")) or []
        for facts_file in sorted((root / SPEC_SUBDIR).glob("*-facts.md"))
    }
    known = {fact["id"]: fact["status"] for facts in fact_sets.values() for fact in facts}

    for facts_file, facts in fact_sets.items():
        design = facts_file.with_name(facts_file.name.replace("-facts.md", "-design.md"))
        spec = expand_ranges(design.read_text(encoding="utf-8")) if design.exists() else ""

        for fact in facts:
            fault = supersession_fault(fact, known)
            if fault is not None:
                ambiguous.append(fault)
            verdict = _process_fact(
                fact,
                spec,
                args,
                selected,
                reports,
                root=root,
                vitest_root=args.vitest_root,
                excluded=excluded,
                forms=forms,
                runner_forms=runner_forms,
                release_reports=project.release_reports,
                members=members,
            )
            if verdict.orphan is not None:
                orphans.append(verdict.orphan)
            if verdict.ambiguous is not None:
                ambiguous.append(verdict.ambiguous)
            if verdict.failed is not None:
                failed.append(verdict.failed)
            if verdict.not_run is not None:
                not_run.append(verdict.not_run)

    if orphans:
        print(f"✗ orphan facts (missing from the design): {', '.join(orphans)}")
    if ambiguous:
        print(f"✗ ambiguous checks: {', '.join(ambiguous)}")
    if failed:
        print(f"✗ red facts: {', '.join(failed)}")
    for entry in not_run:
        print(f"- not run: {entry}")
    if not orphans and not ambiguous and not failed:
        print("✓ no orphan fact, no ambiguous check" + ("" if args.orphans else ", no red fact"))
    return 1 if failed or orphans or ambiguous else 0


def main(argv: Sequence[str] | None = None, members: cargo.Members | None = None) -> int:
    return run(build_parser().parse_args(argv), members)


if __name__ == "__main__":
    sys.exit(main())
