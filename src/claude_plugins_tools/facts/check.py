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
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

import yaml

from claude_plugins_tools.facts import cargo
from claude_plugins_tools.facts.orphans import cited_ids
from claude_plugins_tools.facts.reports import (
    DuplicateReportError,
    MalformedReportError,
    Reports,
    load_reports,
    red_tests,
)
from claude_plugins_tools.facts.schema import schema_faults
from claude_plugins_tools.facts.selectors import (
    DEFAULT_VITEST_ROOT,
    RUNNERS,
    runner_of,
    selector_fault,
    split_parts,
)
from claude_plugins_tools.project import Project, ProjectError, load_project

SPEC_SUBDIR = Path("docs") / "superpowers" / "specs"
RANGE_PATTERN = re.compile(r"([A-Z]{2,4})-(\d{3}) (?:à|to) \1-(\d{3})")
MARKER_PATTERN = re.compile(r"(?:^|\s)-m\s+(\w+)")
# The bare gate stays local: Playwright needs an end-to-end stack (services,
# a built front end, browsers), so it runs only when named explicitly.
#: The statuses --implemented does not list as pending: judged, or replaced.
LEDGER_CLOSED = ("@implemented", "@superseded")
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


def _process_fact(  # noqa: PLR0911, PLR0912, PLR0913 — one return per skip rule, one knob per option
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
    cited: set[str] | None = None,
) -> Verdict:
    """Audit one fact, then judge it: from `reports` when given, else by
    running its check if selected. `excluded` lists, without judging or running,
    a fact whose `requires` names one of its resources. A fact is traced by `cited`
    (the ids on the specs' `*Facts :*` lines) when given, else by `spec`, the text of
    its sibling design."""
    traced = fact["id"] in (spec if cited is None else cited)
    orphan = None if traced else fact["id"]
    # Its test may be gone: the successor carries the guarantee now.
    if fact["status"] == "@superseded":
        return Verdict(orphan)
    check = fact.get("check")
    if not isinstance(check, str) or not check.strip():
        # A draft or spec fact may have none yet; an implemented one claims a test.
        return Verdict(
            orphan, f"{fact['id']} (no check)" if fact["status"] == "@implemented" else None
        )
    ambiguous = None
    # Audited in every mode, --orphans included: running the check cannot
    # reveal the fault, so skipping it in the cheap mode would leave the trap
    # armed exactly where it is cheapest to spot. A @draft fact is exempt:
    # its test is not written yet by definition.
    if fact["status"] != "@draft":
        faults = [
            selector_fault(
                check,
                root,
                vitest_root,
                forms,
                runner_forms=runner_forms,
                fact_id=str(fact["id"]),
                members=members,
            )
        ]
        if excluded:
            faults.append(requires_fault(fact))
        fault = next((fault for fault in faults if fault is not None), None)
        if fault is not None:
            ambiguous = f"{fact['id']} ({fault})"
    if args.orphans or fact["status"] == "@draft":
        return Verdict(orphan, ambiguous)
    if args.implemented and fact["status"] != "@implemented":
        return Verdict(orphan, ambiguous)
    parts = split_parts(check)
    required = fact.get("requires", [])
    if reports is not None and isinstance(required, list) and excluded & set(required):
        needs = ", ".join(sorted(map(str, required)))
        print(f"- {fact['id']} [{fact['status']}] not run (requires: {needs}): {fact['statement']}")
        return Verdict(orphan, ambiguous)
    if reports is not None and all(runner_of(part, runner_forms) == "swift" for part in parts):
        # Audited for form above; no report holds a swift test, so it is not judged.
        print(f"- {fact['id']} [{fact['status']}] not gated (swift): {fact['statement']}")
        return Verdict(orphan, ambiguous)
    if reports is not None:
        red = red_tests(check, reports, runner_forms, release_reports)
        print(f"{'✗' if red else '✓'} {fact['id']} [{fact['status']}] {fact['statement']}")
        for test in red:
            print(f"    {test.test}: {test.reason}" + (f" ({test.job})" if test.job else ""))
        return Verdict(orphan, ambiguous, fact["id"] if red else None)
    if not {runner_of(part, runner_forms) for part in parts} <= selected:
        return Verdict(orphan, ambiguous)
    if isinstance(required, list) and excluded & set(required):
        entry = f"{fact['id']} (requires: {', '.join(sorted(map(str, required)))})"
        return Verdict(orphan, ambiguous, None, entry)
    # A check is a simple command, never a shell line: splitting it rather
    # than interpreting it closes the surface at no cost. A compound check
    # (pipe, redirection) fails here, visibly, which is the right moment to
    # decide whether it belongs in a fact.
    passed = run_check(check, root)
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
        "--only",
        action="append",
        default=[],
        metavar="ID",
        help="judge only this fact; repeatable; an unknown id is an error",
    )
    parser.add_argument(
        "--owner",
        metavar="NAME",
        help="judge only the facts whose owner is NAME ([facts] owner = true)",
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


@dataclass
class Findings:
    """What the pass over the fact-sets found, by kind."""

    failed: list[str] = field(default_factory=list)
    orphans: list[str] = field(default_factory=list)
    ambiguous: list[str] = field(default_factory=list)
    not_run: list[str] = field(default_factory=list)
    pending: list[str] = field(default_factory=list)
    schema: list[str] = field(default_factory=list)
    dangling: list[str] = field(default_factory=list)

    def add(self, verdict: Verdict) -> None:
        for found, kind in (
            (verdict.orphan, self.orphans),
            (verdict.ambiguous, self.ambiguous),
            (verdict.failed, self.failed),
            (verdict.not_run, self.not_run),
        ):
            if found is not None:
                kind.append(found)

    def print(self, orphans_only: bool) -> int:
        """Say what was found, and the exit code."""
        for fault in self.schema:
            print(f"✗ schema: {fault}")
        if self.dangling:
            print(f"✗ dangling (cited, defined by no fact): {', '.join(self.dangling)}")
        if self.orphans:
            print(f"✗ orphan facts (missing from the design): {', '.join(self.orphans)}")
        if self.ambiguous:
            print(f"✗ ambiguous checks: {', '.join(self.ambiguous)}")
        if self.failed:
            print(f"✗ red facts: {', '.join(self.failed)}")
        for entry in self.not_run:
            print(f"- not run: {entry}")
        for entry in self.pending:
            print(f"- pending: {entry}")
        bad = self.failed or self.orphans or self.ambiguous or self.schema or self.dangling
        if not bad:
            print(
                "✓ no orphan fact, no ambiguous check" + ("" if orphans_only else ", no red fact")
            )
        return 1 if bad else 0


def _usage_error(args: argparse.Namespace, project: Project, known: Mapping[str, object]) -> str:
    """What is wrong with --owner or --only for this project, or the empty string."""
    if args.owner is not None and not project.owner:
        return "--owner needs `owner = true` under [facts] in .claude/project.toml"
    if unknown := [fact_id for fact_id in args.only if fact_id not in known]:
        return f"unknown fact id in --only: {', '.join(unknown)}"
    return ""


def _kept(fact: Mapping[str, object], args: argparse.Namespace) -> bool:
    """Whether --only and --owner keep this fact."""
    if args.only and fact["id"] not in args.only:
        return False
    return args.owner is None or fact.get("owner") == args.owner


def run(args: argparse.Namespace, members: cargo.Members | None = None) -> int:
    """The gate for parsed `args`; the exit code. `members` replaces `cargo metadata`."""
    root = args.root.resolve()
    try:
        project = load_project(root)
    except ProjectError as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1
    try:
        reports = _reports_of(args.reports)
    except DuplicateReportError as error:
        print(f"✗ two reports for job {error.job}")
        return 1
    except MalformedReportError as error:
        print(f"✗ unreadable report: {error}")
        return 1

    raw_sets = {
        facts_file: yaml.safe_load(facts_file.read_text(encoding="utf-8")) or []
        for facts_file in sorted((root / SPEC_SUBDIR).glob("*-facts.md"))
    }
    fact_sets = {
        facts_file: [fact for fact in facts if isinstance(fact, dict)]
        for facts_file, facts in raw_sets.items()
    }
    known = {
        fact["id"]: fact.get("status")
        for facts in fact_sets.values()
        for fact in facts
        if "id" in fact
    }
    if usage := _usage_error(args, project, known):
        print(f"✗ {usage}", file=sys.stderr)
        return 2

    found = Findings()
    seen: set[str] = set()
    for facts in raw_sets.values() if project.schema else ():
        found.schema += schema_faults(facts, project.schema, seen)
    cited = cited_ids(root / SPEC_SUBDIR) if project.orphans == "facts-lines" else None
    found.dangling = sorted(cited - set(known)) if cited is not None else []
    options = {
        "root": root,
        "vitest_root": args.vitest_root,
        "excluded": frozenset(name for name in args.exclude_requires.split(",") if name),
        "forms": project.check_forms,
        "runner_forms": project.runner_forms,
        "release_reports": project.release_reports,
        "members": _members_of(root, members),
        "cited": cited,
    }

    for facts_file, facts in fact_sets.items():
        design = facts_file.with_name(facts_file.name.replace("-facts.md", "-design.md"))
        spec = expand_ranges(design.read_text(encoding="utf-8")) if design.exists() else ""

        for fact in facts:
            if not {"id", "status", "statement"} <= set(fact):
                found.ambiguous.append(f"{fact.get('id', '<entry>')} (no id, status or statement)")
                continue
            if not _kept(fact, args):
                continue
            if args.implemented and not args.orphans and fact["status"] not in LEDGER_CLOSED:
                found.pending.append(f"{fact['id']} [{fact['status']}]")
            fault = supersession_fault(fact, known)
            if fault is not None:
                found.ambiguous.append(fault)
            found.add(_process_fact(fact, spec, args, args.runner, reports, **options))
    return found.print(args.orphans)


def main(argv: Sequence[str] | None = None, members: cargo.Members | None = None) -> int:
    return run(build_parser().parse_args(argv), members)


if __name__ == "__main__":
    sys.exit(main())
