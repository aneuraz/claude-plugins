import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from claude_plugins_tools.facts import check as facts_check

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"


def test_an_agent_selector_resolves_under_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test = tmp_path / "agent" / "tests" / "x.test.ts"
    test.parent.mkdir(parents=True)
    test.write_text('it("APP-001 does it", () => {});\n', encoding="utf-8")
    check = 'pnpm -C agent exec vitest run tests/x.test.ts -t "APP-001"'
    assert facts_check.selector_fault(check, tmp_path) is None
    missing = 'pnpm -C agent exec vitest run tests/y.test.ts -t "APP-001"'
    assert facts_check.selector_fault(missing, tmp_path) == "agent/tests/y.test.ts does not exist"


def test_an_agent_selector_naming_two_tests_is_a_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    test = tmp_path / "agent" / "tests" / "x.test.ts"
    test.parent.mkdir(parents=True)
    test.write_text('it("APP-001 a", f);\nit("APP-001 b", f);\n', encoding="utf-8")
    check = 'pnpm -C agent exec vitest run tests/x.test.ts -t "APP-001"'
    assert (
        facts_check.selector_fault(check, tmp_path)
        == "APP-001 names 2 tests in agent/tests/x.test.ts"
    )


def _specs(root: Path) -> Path:
    """The directory `cpt facts` reads fact-sets from, under `root`."""
    specs = root / "docs" / "superpowers" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    return specs


def test_runner_of_reads_the_tool() -> None:
    assert facts_check.runner_of("uv run pytest tests/a.py::t -v") == "pytest"
    vitest_check = 'pnpm -C agent exec vitest run tests/x.test.ts -t "APP-1"'
    assert facts_check.runner_of(vitest_check) == "vitest"
    playwright_check = 'pnpm -C agent exec playwright test tests/e2e/x.spec.ts -g "APP-1"'
    assert facts_check.runner_of(playwright_check) == "playwright"


def test_runner_of_matches_tokens_not_substrings() -> None:
    """A path or flag containing "pytest" as a substring must not be read as
    the pytest runner: only an exact argv token counts."""
    assert facts_check.runner_of("uv run pytest-cov tests/a.py") == "unknown"
    assert facts_check.runner_of("cat tests/pytest_notes.txt") == "unknown"


def test_an_unknown_runner_is_a_selector_fault(tmp_path: Path) -> None:
    """A genuine file::function selector, invoked by a tool outside RUNNERS,
    is still a fault: nothing would ever select it to run."""
    check = "tox -e py agent/tests/test_skills.py::test_no_claude_code_subagent"
    assert facts_check.selector_fault(check, tmp_path) is not None


def test_a_red_check_reports_false(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"runner said no", stderr=b"trace"
    )
    monkeypatch.setattr(facts_check.subprocess, "run", lambda *_args, **_kwargs: fake)
    assert facts_check.run_check("uv run pytest tests/a.py::t -v", Path()) is False


def test_a_red_check_prints_the_runner_output_it_captured(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    fake = subprocess.CompletedProcess(
        args=[], returncode=1, stdout=b"runner said no", stderr=b"trace"
    )
    monkeypatch.setattr(facts_check.subprocess, "run", lambda *_args, **_kwargs: fake)
    facts_check.run_check("uv run pytest tests/a.py::t -v", Path())
    out = capsys.readouterr().out
    assert "runner said no" in out
    assert "trace" in out


def test_a_non_selected_runner_is_audited_but_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """--runner pytest on a vitest fact still checks it for orphan and
    selector faults, but never calls its check — no Node, no agent checkout
    needed to audit it."""
    test = tmp_path / "agent" / "tests" / "x.test.ts"
    test.parent.mkdir(parents=True)
    test.write_text('it("APP-001 does it", () => {});\n', encoding="utf-8")
    (_specs(tmp_path) / "x-design.md").write_text(
        "nothing relevant in this design\n", encoding="utf-8"
    )
    (_specs(tmp_path) / "x-facts.md").write_text(
        '- id: APP-001\n  status: "@implemented"\n  statement: s\n'
        '  check: "pnpm -C agent exec vitest run tests/x.test.ts -t \\"APP-001\\""\n',
        encoding="utf-8",
    )

    def fail_if_called(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
        raise AssertionError("a non-selected runner's check must not run")

    monkeypatch.setattr(facts_check.subprocess, "run", fail_if_called)
    assert facts_check.main(["--runner", "pytest", "--root", str(tmp_path)]) == 1
    out = capsys.readouterr().out
    assert "✗ orphan facts (missing from the design): APP-001" in out
    assert "ambiguous checks" not in out


def test_runner_rejects_a_name_outside_runners() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runner", type=facts_check._runner_list)
    with pytest.raises(SystemExit):
        parser.parse_args(["--runner", "eslint"])


def test_a_superseded_fact_needs_an_implemented_successor() -> None:
    known = {"RCP-001": "@implemented", "RCP-002": "@draft"}
    fact = {"id": "SUR-001", "status": "@superseded"}
    assert facts_check.supersession_fault(fact, known) == "SUR-001 has no superseded_by"
    assert (
        facts_check.supersession_fault({**fact, "superseded_by": "RCP-999"}, known)
        == "SUR-001 is superseded by RCP-999, which does not exist"
    )
    assert (
        facts_check.supersession_fault({**fact, "superseded_by": "RCP-002"}, known)
        == "SUR-001 is superseded by RCP-002, which is @draft"
    )
    assert facts_check.supersession_fault({**fact, "superseded_by": "RCP-001"}, known) is None
    assert (
        facts_check.supersession_fault({**fact, "superseded_by": ["RCP-001", "RCP-002"]}, known)
        == "SUR-001 is superseded by RCP-002, which is @draft"
    )
    assert (
        facts_check.supersession_fault({**fact, "superseded_by": []}, known)
        == "SUR-001 has no superseded_by"
    )
    assert facts_check.supersession_fault({**fact, "superseded_by": ["RCP-001"]}, known) is None
    assert facts_check.supersession_fault({"id": "X-001", "status": "@implemented"}, known) is None


def test_a_superseded_fact_is_neither_run_nor_audited(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ran: list[str] = []
    monkeypatch.setattr(facts_check, "run_check", lambda check, _root: ran.append(check) or True)
    args = argparse.Namespace(orphans=False, implemented=False)
    fact = {
        "id": "SUR-001",
        "status": "@superseded",
        "superseded_by": "RCP-001",
        "check": 'pnpm -C agent exec vitest run tests/gone.test.ts -t "SUR-001"',
        "statement": "s",
    }
    verdict = facts_check._process_fact(fact, "SUR-001", args, {"vitest"}, root=Path())
    assert verdict == facts_check.Verdict()
    assert ran == []


_FIXTURE_TESTS = """
import pytest

def test_pass(): pass
def test_fail(): assert False
@pytest.mark.skip
def test_skip(): pass
@pytest.mark.xfail
def test_xfail(): assert False
@pytest.mark.xfail
def test_xpass(): pass
@pytest.fixture
def broken(): raise RuntimeError
def test_error(broken): pass
@pytest.fixture
def late():
    yield
    raise RuntimeError
def test_late(late): pass
@pytest.mark.parametrize("case", ["a", "b"])
def test_cases(case): pass
def test_subtests(subtests):
    with subtests.test("first"):
        pass
    with subtests.test("second"):
        assert False
"""


def test_a_report_records_node_ids_and_six_outcomes(tmp_path: Path) -> None:
    """FGT-011."""
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    (tmp_path / "test_fixture.py").write_text(_FIXTURE_TESTS, encoding="utf-8")
    out = tmp_path / "out" / "row.json"
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"} | {"PYTHONPATH": str(SRC)}
    subprocess.run(  # noqa: S603 — argv built here, no shell
        [
            sys.executable,
            "-m",
            "pytest",
            "-p",
            "claude_plugins_tools.facts.report",
            "-p",
            "no:cacheprovider",
            f"--facts-report={out}",
            "--rootdir",
            str(tmp_path),
            str(tmp_path),
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        check=False,
    )
    assert json.loads(out.read_text(encoding="utf-8")) == {
        "test_fixture.py::test_pass": "passed",
        "test_fixture.py::test_fail": "failed",
        "test_fixture.py::test_skip": "skipped",
        "test_fixture.py::test_xfail": "xfailed",
        "test_fixture.py::test_xpass": "xpassed",
        "test_fixture.py::test_error": "error",
        "test_fixture.py::test_late": "error",
        "test_fixture.py::test_cases[a]": "passed",
        "test_fixture.py::test_cases[b]": "passed",
        "test_fixture.py::test_subtests": "failed",
    }


C = "uv run --all-packages --exact pytest tests/t.py::a -v"
IMPLEMENTED_CHECK = "uv run --all-packages --exact pytest tests/t.py::a -v"
SPEC_CHECK = "uv run --all-packages --exact pytest tests/t.py::b -v"


def _no_subprocess(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
    raise AssertionError("the gate must not run a check under --reports")


def _gate(  # noqa: PLR0913 — each keyword is one knob of the fixture
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    check: str,
    reports: dict[str, dict[str, str]] | None,
    *,
    design: str = "FGT-900",
    test_file: str = "tests/t.py",
    functions: tuple[str, ...] = ("a", "b"),
    status: str = "@implemented",
    extra_args: tuple[str, ...] = (),
) -> tuple[int, str]:
    """One fact FGT-900 with `status` and `check`, its test file defining `functions`;
    each report written as reports/facts-report-<job>/<job>.json (None: no reports/
    directory at all); then main() with --reports reports and `extra_args`."""
    (_specs(tmp_path) / "x-design.md").write_text(f"{design}\n", encoding="utf-8")
    fact = {"id": "FGT-900", "status": status, "statement": "s", "check": check}
    (_specs(tmp_path) / "x-facts.md").write_text(yaml.safe_dump([fact]), encoding="utf-8")
    test = tmp_path / test_file
    test.parent.mkdir(parents=True, exist_ok=True)
    test.write_text("".join(f"def {name}(): pass\n" for name in functions), encoding="utf-8")
    if reports is not None:
        (tmp_path / "reports").mkdir(exist_ok=True)
        for job, report in reports.items():
            path = tmp_path / "reports" / f"facts-report-{job}" / f"{job}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(facts_check.subprocess, "run", _no_subprocess)
    code = facts_check.main(["--reports", "reports", "--root", str(tmp_path), *extra_args])
    return code, capsys.readouterr().out


def test_a_fact_whose_tests_passed_is_green(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-001."""
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {"suites-x": {"tests/t.py::a": "passed"}})
    assert code == 0
    assert "✓ FGT-900" in out


def test_a_test_in_no_report_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-002."""
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {"suites-x": {"tests/t.py::b": "passed"}})
    assert code == 1
    assert "tests/t.py::a: not run" in out


def test_a_skipped_test_is_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-003."""
    reports = {
        "suites-x": {"tests/t.py::a": "passed"},
        "integration": {"tests/t.py::a": "skipped"},
    }
    code, out = _gate(tmp_path, monkeypatch, capsys, C, reports)
    assert code == 1
    assert "tests/t.py::a: skipped (integration)" in out


def test_a_failed_or_errored_test_is_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-004."""
    for outcome in ("failed", "error"):
        code, out = _gate(
            tmp_path, monkeypatch, capsys, C, {"suites-x": {"tests/t.py::a": outcome}}
        )
        assert code == 1
        assert "tests/t.py::a: failed (suites-x)" in out


def test_an_xfail_or_xpass_is_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-005."""
    for outcome in ("xfailed", "xpassed"):
        code, out = _gate(
            tmp_path, monkeypatch, capsys, C, {"suites-x": {"tests/t.py::a": outcome}}
        )
        assert code == 1
        assert "tests/t.py::a: xfail (suites-x)" in out


def test_every_case_of_a_parametrised_test_must_pass(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-006."""
    report = {"tests/t.py::a[x]": "passed", "tests/t.py::a[y]": "skipped"}
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {"suites-x": report})
    assert code == 1
    assert "tests/t.py::a[y]: skipped (suites-x)" in out


def test_a_selector_naming_one_case_requires_that_case_alone(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-007."""
    check = "uv run --all-packages --exact pytest tests/t.py::a[x] -v"
    report = {"tests/t.py::a[x]": "passed", "tests/t.py::a[y]": "failed"}
    code, _ = _gate(tmp_path, monkeypatch, capsys, check, {"suites-x": report})
    assert code == 0


def test_a_check_naming_several_tests_needs_each(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-008."""
    check = "uv run --all-packages --exact pytest tests/t.py::a tests/t.py::b -v"
    code, out = _gate(
        tmp_path, monkeypatch, capsys, check, {"suites-x": {"tests/t.py::a": "passed"}}
    )
    assert code == 1
    assert "tests/t.py::b: not run" in out


def test_a_red_fact_names_its_test_reason_and_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-009."""
    reports = {"suites-candle-core": {"tests/t.py::a": "failed"}}
    _, out = _gate(tmp_path, monkeypatch, capsys, C, reports)
    lines = out.splitlines()
    red = next(i for i, line in enumerate(lines) if line.startswith("✗ FGT-900"))
    assert lines[red + 1] == "    tests/t.py::a: failed (suites-candle-core)"


def test_reports_mode_still_fails_on_an_orphan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-017."""
    code, out = _gate(
        tmp_path,
        monkeypatch,
        capsys,
        C,
        {"suites-x": {"tests/t.py::a": "passed"}},
        design="nothing",
    )
    assert code == 1
    assert "orphan facts" in out


def test_reports_mode_still_fails_on_an_ambiguous_selector(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-018."""
    code, out = _gate(
        tmp_path,
        monkeypatch,
        capsys,
        C,
        {"suites-x": {"tests/t.py::a": "passed"}},
        functions=("a", "a"),
    )
    assert code == 1
    assert "ambiguous checks" in out


def test_reports_mode_keeps_implemented_s_meaning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-021."""
    code, _ = _gate(
        tmp_path, monkeypatch, capsys, C, {}, status="@spec", extra_args=("--implemented",)
    )
    assert code == 0


def test_a_check_with_no_pytest_selector_is_not_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-023."""
    agent_test = tmp_path / "agent" / "tests" / "x.test.ts"
    agent_test.parent.mkdir(parents=True)
    agent_test.write_text('it("FGT-900 x", f);\n', encoding="utf-8")
    check = 'pnpm -C agent exec vitest run tests/x.test.ts -t "FGT-900"'
    code, out = _gate(tmp_path, monkeypatch, capsys, check, {"suites-x": {}})
    assert code == 1
    assert "not run" in out


def test_a_case_id_with_separators_still_matches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    check = "uv run --all-packages --exact pytest tests/t.py::a[p::q/r] -v"
    code, _ = _gate(
        tmp_path, monkeypatch, capsys, check, {"suites-x": {"tests/t.py::a[p::q/r]": "passed"}}
    )
    assert code == 0


def test_an_empty_report_directory_fails_every_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {})
    assert code == 1
    assert "not run" in out


def test_a_missing_report_directory_fails_every_fact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _gate(tmp_path, monkeypatch, capsys, C, None)
    assert code == 1
    assert "not run" in out
    assert "Traceback" not in out


def test_an_unknown_outcome_is_red(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {"suites-x": {"tests/t.py::a": "rerun"}})
    assert code == 1
    assert "unknown outcome rerun" in out


def test_without_reports_each_check_runs_verbatim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """FGT-016: an @implemented, a @spec, a @draft and a @superseded fact; only the
    first two run, each its own check, verbatim."""
    (_specs(tmp_path) / "x-design.md").write_text("FGT-901 to FGT-904\n", encoding="utf-8")
    facts = [
        {"id": "FGT-901", "status": "@implemented", "statement": "s", "check": IMPLEMENTED_CHECK},
        {"id": "FGT-902", "status": "@spec", "statement": "s", "check": SPEC_CHECK},
        {"id": "FGT-903", "status": "@draft", "statement": "s", "check": "draft check"},
        {
            "id": "FGT-904",
            "status": "@superseded",
            "superseded_by": "FGT-901",
            "statement": "s",
            "check": "superseded check",
        },
    ]
    (_specs(tmp_path) / "x-facts.md").write_text(yaml.safe_dump(facts), encoding="utf-8")
    test = tmp_path / "tests" / "t.py"
    test.parent.mkdir()
    test.write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")
    ran: list[str] = []
    monkeypatch.setattr(facts_check, "run_check", lambda check, _root: ran.append(check) or True)
    assert facts_check.main(["--runner", "pytest", "--root", str(tmp_path)]) == 0
    assert ran == [IMPLEMENTED_CHECK, SPEC_CHECK]


def _two_tests(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    test = tmp_path / "tests" / "t.py"
    test.parent.mkdir()
    test.write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")


@pytest.mark.parametrize(
    "check",
    [
        "uv run --all-packages --exact pytest tests/t.py::a -v",
        "uv run --package candle-agent --exact pytest tests/t.py::a tests/t.py::b -v",
        "uv run --all-packages --exact pytest -m integration tests/t.py::a -v",
    ],
)
def test_a_check_in_the_form_is_no_fault(
    check: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _two_tests(tmp_path, monkeypatch)
    assert facts_check.selector_fault(check, tmp_path) is None


def test_a_check_outside_the_form_is_a_fault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """FGT-019."""
    _two_tests(tmp_path, monkeypatch)
    for extra in (
        "-k x",
        "-W error",
        "-p no:randomly",
        "-o addopts=",
        "--deselect tests/t.py::b",
        "-m deid",
        "&& true",
        "--exact --exact",
    ):
        check = f"uv run --all-packages --exact pytest tests/t.py::a -v {extra}"
        assert (
            facts_check.selector_fault(check, tmp_path)
            == f"a token outside the check's form in {check!r}"
        )
    assert (
        facts_check.selector_fault("uv run --exact pytest tests/t.py::a -v", tmp_path) is not None
    )


def test_two_reports_for_one_job_fail_the_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A second report of one job must not silently replace the first."""
    for artifact, outcome in (("a", "failed"), ("b", "passed")):
        path = tmp_path / "reports" / artifact / "suites-x.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"tests/t.py::a": outcome}), encoding="utf-8")
    code, out = _gate(tmp_path, monkeypatch, capsys, C, {})
    assert code == 1
    assert "✗ two reports for job suites-x" in out
