"""The cargo and swift check forms: judged from nextest reports, audited statically, and the
`&&` conjunction across runners. Real `capture` check strings stand for the grammar."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
import yaml

from claude_plugins_tools.facts import cargo, convert
from claude_plugins_tools.facts import check as facts_check
from claude_plugins_tools.facts.reports import Entry, load_reports, red_tests

# Copied literally from capture's fact-sets.
BACKUP = (
    "cargo test -p cap --test backup -- backup_writes_a_tree_and_a_recoverable_key "
    "backup_fails_when_the_key_cannot_be_sealed"
)
BENCH = "cargo test -p cap --release --test bench_ingest -- p95_under_100ms"
LIB = "cargo test -p store --lib -- spool::"
PATH_FILTER = (
    "cargo test -p store --test spool -- spool::a_managed_blob_name_is_always_a_single_component"
)
SWIFT = "swift test --package-path agent --filter 'ScreenshotConfigTests'"
CONJUNCTION = (
    "cargo test -p cap --test containment && cargo test -p store --test spool -- "
    "a_managed_blob_name_is_always_a_single_component "
    "a_captured_at_that_is_not_rfc3339_invalidates_the_entry"
)
TOML = """\
[facts]
release_reports = ["rust-release"]

[facts.check_forms]
cargo = [
  "cargo test -p * --test *",
  "cargo test -p * --test * --release",
  "cargo test -p * --lib",
]
swift = ["swift test --package-path agent --filter *"]
"""
SOURCES = {
    "crates/cap/tests/backup.rs": "fn backup_writes_a_tree_and_a_recoverable_key() {}\n"
    "fn backup_fails_when_the_key_cannot_be_sealed() {}\n",
    "crates/cap/tests/bench_ingest.rs": "fn p95_under_100ms() {}\n",
    "crates/cap/tests/containment.rs": "fn x() {}\n",
    "crates/store/src/lib.rs": "mod spool;\nfn y() {}\n",
    "crates/store/tests/spool.rs": "fn a_managed_blob_name_is_always_a_single_component() {}\n"
    "fn a_captured_at_that_is_not_rfc3339_invalidates_the_entry() {}\n",
}


def _members(root: Path):
    return lambda: {"cap": root / "crates" / "cap", "store": root / "crates" / "store"}


def _project(root: Path, check: str, status: str = "@implemented", toml: str = TOML) -> None:
    specs = root / "docs" / "superpowers" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "x-design.md").write_text("CAP-001\n", encoding="utf-8")
    fact = {"id": "CAP-001", "status": status, "statement": "s", "check": check}
    (specs / "x-facts.md").write_text(yaml.safe_dump([fact]), encoding="utf-8")
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "project.toml").write_text(toml, encoding="utf-8")
    for file, text in SOURCES.items():
        (root / file).parent.mkdir(parents=True, exist_ok=True)
        (root / file).write_text(text, encoding="utf-8")


def _report(root: Path, job: str, binary: str, *tests: tuple[str, str]) -> None:
    entries = {
        f"{binary}::{name}": {"title": name, "outcome": outcome, "binary": binary}
        for name, outcome in tests
    }
    path = root / "reports" / f"{job}.json"
    path.parent.mkdir(exist_ok=True)
    existing = json.loads(path.read_text("utf-8")) if path.exists() else {}
    path.write_text(json.dumps({**existing, **entries}), encoding="utf-8")


def _gate(root: Path, capsys: pytest.CaptureFixture[str], *extra: str) -> tuple[int, str]:
    argv = ["--root", str(root), "--reports", str(root / "reports"), *extra]
    code = facts_check.main(argv, members=_members(root))
    return code, capsys.readouterr().out


def _red(check: str, root: Path, **kwargs: object) -> list[tuple[str, str]]:
    forms = facts_check.load_project(root)
    reports = load_reports(root / "reports")
    release = forms.release_reports
    return [(r.test, r.reason) for r in red_tests(check, reports, forms.runner_forms, release)]


# --- judging --------------------------------------------------------------------------


def test_every_filter_selects_an_entry_and_all_passed(tmp_path: Path) -> None:
    _project(tmp_path, BACKUP)
    _report(
        tmp_path,
        "debug",
        "cap::backup",
        ("backup_writes_a_tree_and_a_recoverable_key", "passed"),
        ("backup_fails_when_the_key_cannot_be_sealed", "passed"),
        ("unrelated", "failed"),
    )
    assert _red(BACKUP, tmp_path) == []


def test_a_filter_is_a_substring_of_the_test_path(tmp_path: Path) -> None:
    _project(tmp_path, PATH_FILTER)
    _report(
        tmp_path,
        "debug",
        "store::spool",
        ("spool::a_managed_blob_name_is_always_a_single_component", "passed"),
    )
    assert _red(PATH_FILTER, tmp_path) == []
    check = "cargo test -p store --test spool -- always_a_single"
    assert _red(check, tmp_path) == []


def test_a_filter_selecting_nothing_is_not_run_even_when_another_passes(tmp_path: Path) -> None:
    _project(tmp_path, BACKUP)
    _report(
        tmp_path,
        "debug",
        "cap::backup",
        ("backup_writes_a_tree_and_a_recoverable_key", "passed"),
    )
    assert _red(BACKUP, tmp_path) == [
        ("cap::backup backup_fails_when_the_key_cannot_be_sealed", "not run")
    ]


def test_no_filter_selects_the_whole_binary(tmp_path: Path) -> None:
    _project(tmp_path, "cargo test -p cap --test backup")
    _report(tmp_path, "debug", "cap::backup", ("a", "passed"), ("b", "failed"))
    _report(tmp_path, "debug", "cap::other", ("c", "failed"))
    assert _red("cargo test -p cap --test backup", tmp_path) == [("cap::backup::b", "failed")]


def test_no_entry_in_the_binary_is_not_run(tmp_path: Path) -> None:
    _project(tmp_path, "cargo test -p cap --test backup")
    _report(tmp_path, "debug", "cap::other", ("c", "passed"))
    assert _red("cargo test -p cap --test backup", tmp_path) == [("cap::backup", "not run")]


def test_lib_selects_the_package_binary_only(tmp_path: Path) -> None:
    _project(tmp_path, LIB)
    _report(tmp_path, "debug", "store", ("spool::a", "passed"))
    _report(tmp_path, "debug", "store::spool", ("spool::b", "failed"))
    assert _red(LIB, tmp_path) == []
    assert _red("cargo test -p store --lib", tmp_path) == []


def test_release_reads_only_the_release_reports(tmp_path: Path) -> None:
    _project(tmp_path, BENCH)
    _report(tmp_path, "rust-debug", "cap::bench_ingest", ("p95_under_100ms", "failed"))
    assert _red(BENCH, tmp_path) == [("cap::bench_ingest p95_under_100ms", "not run")]
    _report(tmp_path, "rust-release", "cap::bench_ingest", ("p95_under_100ms", "passed"))
    assert _red(BENCH, tmp_path) == []
    # and the debug run does not read the release report
    _project(tmp_path, "cargo test -p cap --test bench_ingest")
    assert _red("cargo test -p cap --test bench_ingest", tmp_path) == [
        ("cap::bench_ingest::p95_under_100ms", "failed")
    ]


def test_a_release_check_without_declared_release_reports_is_not_run(tmp_path: Path) -> None:
    _project(tmp_path, BENCH, toml=TOML.replace('release_reports = ["rust-release"]\n', ""))
    _report(tmp_path, "rust-release", "cap::bench_ingest", ("p95_under_100ms", "passed"))
    assert _red(BENCH, tmp_path) == [("cap::bench_ingest p95_under_100ms", "not run")]


def test_release_reports_are_named_by_file_stem(tmp_path: Path) -> None:
    _project(tmp_path, BENCH, toml=TOML.replace("rust-release", "rust-release"))
    _report(tmp_path, "rust-release", "cap::bench_ingest", ("p95_under_100ms", "passed"))
    assert _red(BENCH, tmp_path) == []


def test_the_conjunction_needs_every_part(tmp_path: Path) -> None:
    _project(tmp_path, CONJUNCTION)
    _report(tmp_path, "debug", "cap::containment", ("c", "passed"))
    _report(
        tmp_path,
        "debug",
        "store::spool",
        ("a_managed_blob_name_is_always_a_single_component", "passed"),
    )
    assert _red(CONJUNCTION, tmp_path) == [
        ("store::spool a_captured_at_that_is_not_rfc3339_invalidates_the_entry", "not run")
    ]
    _report(
        tmp_path,
        "debug",
        "store::spool",
        ("a_captured_at_that_is_not_rfc3339_invalidates_the_entry", "failed"),
    )
    assert _red(CONJUNCTION, tmp_path) == [
        ("store::spool::a_captured_at_that_is_not_rfc3339_invalidates_the_entry", "failed")
    ]


def test_the_conjunction_applies_to_pytest_and_by_id_parts(tmp_path: Path) -> None:
    reports = {
        "j": {
            "t.py::a": load_reports_entry("t.py::a", "passed"),
            "f": load_reports_entry("f", "passed", title="APP-001 x", file="a.test.ts"),
        }
    }
    check = 'pytest t.py::a && pnpm exec vitest run a.test.ts -t "APP-001"'
    forms = {"vitest": ('pnpm exec vitest run <file> -t "<id>"',)}
    assert red_tests(check, reports, forms) == []
    missing = 'pytest t.py::a && pytest t.py::zzz && pnpm exec vitest run a.test.ts -t "APP-001"'
    assert [r.reason for r in red_tests(missing, reports, forms)] == ["not run"]
    other = 'pytest t.py::a && pnpm exec vitest run b.test.ts -t "APP-001"'
    assert [r.reason for r in red_tests(other, reports, forms)] == ["not run"]


def load_reports_entry(
    key: str, outcome: str, *, title: str | None = None, file: str | None = None
):
    return Entry(key, title or key, outcome, file or key.partition("::")[0])


def test_the_gate_is_red_on_a_missing_report_never_green(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, BACKUP)
    code, out = _gate(tmp_path, capsys, "--implemented")
    assert code == 1
    assert "not run" in out
    assert "✓ CAP-001" not in out


def test_the_gate_is_green_when_reports_prove_the_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, BACKUP)
    _report(
        tmp_path,
        "debug",
        "cap::backup",
        ("backup_writes_a_tree_and_a_recoverable_key", "passed"),
        ("backup_fails_when_the_key_cannot_be_sealed", "passed"),
    )
    _report(tmp_path, "rust-release", "cap::bench_ingest", ("p95_under_100ms", "passed"))
    assert _gate(tmp_path, capsys, "--implemented")[0] == 0


def test_a_swift_fact_is_audited_but_never_judged(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, SWIFT)
    code, out = _gate(tmp_path, capsys, "--implemented")
    assert code == 0
    assert "not gated (swift)" in out
    assert "CAP-001 [" not in out.replace("- CAP-001 [", "")


def test_a_swift_part_does_not_hide_a_cargo_part(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, f"{BACKUP} && {SWIFT}")
    code, _ = _gate(tmp_path, capsys, "--implemented")
    assert code == 1  # the cargo part selects nothing


# --- static audit ---------------------------------------------------------------------


def _fault(check: str, root: Path, toml: str = TOML) -> str | None:
    _project(root, check, toml=toml)
    project = facts_check.load_project(root)
    return facts_check.selector_fault(
        check,
        root,
        runner_forms=project.runner_forms,
        fact_id="CAP-001",
        members=_members(root),
    )


@pytest.mark.parametrize("check", [BACKUP, BENCH, LIB, PATH_FILTER, SWIFT, CONJUNCTION])
def test_real_capture_checks_parse_and_audit(tmp_path: Path, check: str) -> None:
    assert _fault(check, tmp_path) is None


def test_a_missing_test_file_is_a_fault(tmp_path: Path) -> None:
    fault = _fault("cargo test -p cap --test nope", tmp_path)
    assert fault == "tests/nope.rs of cap does not exist"


def test_a_filter_absent_from_the_file_is_a_fault(tmp_path: Path) -> None:
    fault = _fault("cargo test -p cap --test backup -- no_such_test", tmp_path)
    assert "no_such_test" in str(fault)


def test_a_path_filter_is_checked_by_its_last_segment(tmp_path: Path) -> None:
    assert (
        _fault(
            "cargo test -p store --test spool -- zz::yy::"
            "a_managed_blob_name_is_always_a_single_component",
            tmp_path,
        )
        is None
    )
    assert _fault("cargo test -p store --test spool -- spool::nope", tmp_path) is not None


def test_a_lib_filter_is_looked_up_in_src(tmp_path: Path) -> None:
    assert _fault("cargo test -p store --lib -- y", tmp_path) is None
    assert _fault("cargo test -p store --lib -- backup_writes_a_tree", tmp_path) is not None


def test_a_package_outside_the_workspace_is_a_fault(tmp_path: Path) -> None:
    assert _fault("cargo test -p ghost --test x", tmp_path) == "ghost is not a workspace member"


@pytest.mark.parametrize(
    "extra",
    ["--exact", "--ignored", "--nocapture", "--show-output", "--test-threads=1"],
)
def test_flags_after_the_separator_are_refused(tmp_path: Path, extra: str) -> None:
    check = f"cargo test -p cap --test backup -- backup_writes_a_tree_and_a_recoverable_key {extra}"
    assert f"{extra} is outside the cargo form" in str(_fault(check, tmp_path))


@pytest.mark.parametrize(
    "extra", ["--features x", "--all-features", "--bin y", "-q", "--workspace"]
)
def test_flags_before_the_separator_are_refused(tmp_path: Path, extra: str) -> None:
    check = f"cargo test -p cap --test backup {extra}"
    assert "is outside the cargo form" in str(_fault(check, tmp_path))


@pytest.mark.parametrize(
    "check",
    ["cargo test -p cap", "cargo test --test backup", "cargo test -p cap --lib --test backup"],
)
def test_a_target_is_required_once(tmp_path: Path, check: str) -> None:
    assert "are required" in str(_fault(check, tmp_path))


def test_a_non_test_cargo_command_is_a_fault(tmp_path: Path) -> None:
    check = "cargo run -q -p i18n --bin emit-swift -- --check"
    assert "not a `cargo test` check" in str(_fault(check, tmp_path))


def test_a_declared_cargo_form_is_enforced(tmp_path: Path) -> None:
    toml = TOML.replace('  "cargo test -p * --test * --release",\n', "")
    assert "a token outside the check's form" in str(_fault(BENCH, tmp_path, toml))
    assert _fault(BACKUP, tmp_path, toml) is None


def test_swift_needs_a_declared_form_and_matches_it(tmp_path: Path) -> None:
    assert "no swift form is declared" in str(_fault(SWIFT, tmp_path, "[facts]\n"))
    assert "outside the check's form" in str(_fault("swift test --filter X", tmp_path))


def test_the_audit_runs_in_orphans_mode_and_on_every_fact(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, "cargo test -p cap --test nope")
    assert facts_check.main(["--root", str(tmp_path), "--orphans"], members=_members(tmp_path)) == 1
    assert "ambiguous checks" in capsys.readouterr().out


def test_metadata_is_asked_once_and_lazily(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    calls = []

    def provider() -> dict[str, Path]:
        calls.append(1)
        return _members(tmp_path)()

    _project(tmp_path, f"{BACKUP} && {BENCH}")
    facts_check.main(["--root", str(tmp_path), "--orphans"], members=provider)
    assert calls == [1]
    _project(tmp_path, "pytest x.py::f", toml="[facts]\n")
    facts_check.main(["--root", str(tmp_path), "--orphans"], members=provider)
    assert calls == [1]


@pytest.mark.skipif(shutil.which("cargo") is None, reason="needs cargo")
def test_real_cargo_metadata_on_a_scratch_workspace(tmp_path: Path) -> None:
    (tmp_path / "Cargo.toml").write_text('[workspace]\nmembers = ["crates/*"]\nresolver = "2"\n')
    crate = tmp_path / "crates" / "cap"
    (crate / "src").mkdir(parents=True)
    (crate / "Cargo.toml").write_text(
        '[package]\nname = "cap"\nversion = "0.1.0"\nedition = "2021"\n'
    )
    (crate / "src" / "lib.rs").write_text("")
    found = cargo.workspace_members(tmp_path)
    assert found == {"cap": crate.resolve()} or {k: v.resolve() for k, v in found.items()} == {
        "cap": crate.resolve()
    }


# --- local mode and configuration -----------------------------------------------------


def test_local_mode_runs_a_cargo_check_by_exit_code(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _project(tmp_path, BACKUP)
    ran = []

    def fake(argv, **kwargs):
        ran.append(argv)
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    monkeypatch.setattr(facts_check.subprocess, "run", fake)
    assert facts_check.main(["--root", str(tmp_path)], members=_members(tmp_path)) == 0
    assert [a[:2] for a in ran] == [["cargo", "test"]]


def test_local_mode_runs_the_parts_in_order_and_stops_at_a_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    ran = []

    def fake(argv, **kwargs):
        ran.append(argv[2:5])
        return subprocess.CompletedProcess(argv, 1 if "containment" in argv else 0, b"", b"")

    monkeypatch.setattr(facts_check.subprocess, "run", fake)
    assert (
        facts_check.run_check(
            "cargo test -p cap --test containment && cargo test -p x --lib", tmp_path
        )
        is False
    )
    assert len(ran) == 1


def test_project_reads_release_reports(tmp_path: Path) -> None:
    _project(tmp_path, BACKUP)
    assert facts_check.load_project(tmp_path).release_reports == ("rust-release",)
    assert facts_check.load_project(tmp_path).runner_forms["swift"] == (
        "swift test --package-path agent --filter *",
    )


@pytest.mark.parametrize(
    "check",
    [
        "cargo test -p cap --test a --test b -- x",
        "cargo test -p a -p b --lib",
        "cargo test -p a --package b --lib",
        "cargo test -p cap --lib --lib",
        "cargo test -p cap --test backup --release --release",
        "cargo test -p cap --lib --test backup",
    ],
)
def test_a_repeated_or_conflicting_flag_is_a_fault(tmp_path: Path, check: str) -> None:
    assert _fault(check, tmp_path) is not None
    assert isinstance(cargo.parse(check), str)


@pytest.mark.parametrize("tail", ["; true", "|| true", "| cat", "> out"])
def test_a_shell_construct_other_than_and_is_still_a_fault(tmp_path: Path, tail: str) -> None:
    assert _fault(f"{BACKUP} {tail}", tmp_path) is not None


# `cargo nextest run` of a scratch workspace holding the dashed package `cap-app`
# (cargo-nextest 0.9.151): the suite names are the package name, dashes kept.
DASHED_JUNIT = """<?xml version="1.0" encoding="UTF-8"?>
<testsuites name="nextest-run" tests="2" skipped="0" failures="0" errors="0">
    <testsuite name="cap-app::append_revision" tests="1" skipped="0" errors="0" failures="0">
        <testcase name="it_one" classname="cap-app::append_revision" time="0.012"/>
    </testsuite>
    <testsuite name="cap-app" tests="1" skipped="0" errors="0" failures="0">
        <testcase name="lib_one" classname="cap-app" time="0.012"/>
    </testsuite>
</testsuites>
"""


def test_a_dashed_package_is_selected_end_to_end(tmp_path: Path) -> None:
    raw = tmp_path / "junit.xml"
    raw.write_text(DASHED_JUNIT, encoding="utf-8")
    out = tmp_path / "reports" / "debug.json"
    out.parent.mkdir()
    convert.convert("nextest", raw, out)
    reports = load_reports(out.parent)
    assert {e.binary for e in reports["debug"].values()} == {"cap-app", "cap-app::append_revision"}
    for check in (
        "cargo test -p cap-app --test append_revision -- it_one",
        "cargo test -p cap-app --lib -- lib_one",
    ):
        assert red_tests(check, reports) == []
    missing = red_tests("cargo test -p cap-app --lib -- it_one", reports)
    assert [r.reason for r in missing] == ["not run"]
