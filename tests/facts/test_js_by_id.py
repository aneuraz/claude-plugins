"""The by-id rule for vitest and Playwright facts: entries of the check's file whose own
title starts with "<ID> "; at least one, all passed. Forms come from [facts.check_forms]."""

import json
from pathlib import Path

import pytest
import yaml

from claude_plugins_tools.facts import check as facts_check

VITEST = 'pnpm exec vitest run tests/contracts/a.test.ts -t "APP-001"'
PLAYWRIGHT = 'pnpm exec playwright test tests/e2e/b.spec.ts -g "APP-001"'
FORMS = (
    "[facts.check_forms]\nvitest = ['pnpm exec vitest run <file> -t \"<id>\"']\n"
    "playwright = ['pnpm exec playwright test <file> -g \"<id>\"']\n"
)


def _project(root: Path, check: str, tests: dict[str, str], toml: str = FORMS) -> None:
    specs = root / "docs" / "superpowers" / "specs"
    specs.mkdir(parents=True)
    (specs / "x-design.md").write_text("APP-001\n", encoding="utf-8")
    fact = {"id": "APP-001", "status": "@implemented", "statement": "s", "check": check}
    (specs / "x-facts.md").write_text(yaml.safe_dump([fact]), encoding="utf-8")
    (root / ".claude").mkdir()
    (root / ".claude" / "project.toml").write_text(toml, encoding="utf-8")
    for file, text in tests.items():
        (root / file).parent.mkdir(parents=True, exist_ok=True)
        (root / file).write_text(text, encoding="utf-8")


def _entry(file: str, title: str, outcome: str = "passed", describe: str = "") -> dict[str, str]:
    return {"title": title, "outcome": outcome, "file": file}


def _report(root: Path, entries: dict[str, dict[str, str]], job: str = "ui") -> None:
    path = root / "reports" / job / f"{job}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries), encoding="utf-8")


def _gate(root: Path, capsys: pytest.CaptureFixture[str], *extra: str) -> tuple[int, str]:
    code = facts_check.main(["--root", str(root), "--reports", str(root / "reports"), *extra])
    return code, capsys.readouterr().out


TESTS = {"tests/contracts/a.test.ts": 'it("APP-001 does x", () => {});\n'}
KEY = "tests/contracts/a.test.ts::APP-001 does x"


def test_candle_app_s_two_forms_pass(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    tests = {**TESTS, "tests/e2e/b.spec.ts": 'test("APP-001 e2e", async () => {});\n'}
    _project(tmp_path, VITEST, tests)
    for check in (VITEST, PLAYWRIGHT):
        fact = {"id": "APP-001", "status": "@implemented", "statement": "s", "check": check}
        facts = tmp_path / "docs" / "superpowers" / "specs" / "x-facts.md"
        facts.write_text(yaml.safe_dump([fact]), encoding="utf-8")
        _report(
            tmp_path,
            {
                KEY: _entry("tests/contracts/a.test.ts", "APP-001 does x"),
                "tests/e2e/b.spec.ts::APP-001 e2e": _entry("tests/e2e/b.spec.ts", "APP-001 e2e"),
            },
        )
        assert _gate(tmp_path, capsys, "--implemented")[0] == 0


def test_the_fact_is_green_when_every_titled_entry_passed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, TESTS)
    _report(
        tmp_path,
        {
            KEY: _entry("tests/contracts/a.test.ts", "APP-001 does x"),
            "k2": _entry("tests/contracts/a.test.ts", "APP-001 and y"),
            # another id sharing the prefix, another file, a describe named after the id
            "k3": _entry("tests/contracts/a.test.ts", "APP-0011 z", "failed"),
            "k4": _entry("tests/contracts/other.test.ts", "APP-001 w", "failed"),
        },
    )
    code, out = _gate(tmp_path, capsys)
    assert code == 0
    assert "✓ APP-001" in out


@pytest.mark.parametrize("outcome", ["failed", "skipped"])
def test_one_red_entry_makes_the_fact_red(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], outcome: str
) -> None:
    _project(tmp_path, VITEST, TESTS)
    _report(
        tmp_path,
        {
            KEY: _entry("tests/contracts/a.test.ts", "APP-001 does x"),
            "k2": _entry("tests/contracts/a.test.ts", "APP-001 and y", outcome),
        },
    )
    code, out = _gate(tmp_path, capsys)
    assert code == 1
    assert f"k2: {outcome} (ui)" in out


def test_no_entry_is_not_run_and_never_green(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, TESTS)
    _report(tmp_path, {"k": _entry("tests/contracts/other.test.ts", "APP-001 x")})
    code, out = _gate(tmp_path, capsys)
    assert code == 1
    assert "tests/contracts/a.test.ts APP-001: not run" in out


def test_a_missing_report_directory_is_not_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, TESTS)
    code, out = _gate(tmp_path, capsys)
    assert code == 1
    assert "not run" in out


def test_a_describe_named_after_the_id_does_not_stand_for_its_tests(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, TESTS)
    _report(
        tmp_path,
        {"tests/contracts/a.test.ts::APP-001 d > t": _entry("tests/contracts/a.test.ts", "t")},
    )
    assert _gate(tmp_path, capsys)[0] == 1


def test_the_id_must_be_the_facts(tmp_path: Path) -> None:
    check = 'pnpm exec vitest run tests/contracts/a.test.ts -t "APP-002"'
    _project(tmp_path, check, TESTS)
    forms = facts_check.load_project(tmp_path).runner_forms
    fault = facts_check.selector_fault(check, tmp_path, runner_forms=forms, fact_id="APP-001")
    assert fault == "APP-002 is not APP-001"


def test_no_test_carries_the_id(tmp_path: Path) -> None:
    _project(tmp_path, VITEST, {"tests/contracts/a.test.ts": 'it("APP-0011 x", f);\n'})
    forms = facts_check.load_project(tmp_path).runner_forms
    fault = facts_check.selector_fault(VITEST, tmp_path, runner_forms=forms, fact_id="APP-001")
    assert fault == "no test of tests/contracts/a.test.ts has a title starting with APP-001"


def test_the_file_must_exist(tmp_path: Path) -> None:
    _project(tmp_path, VITEST, {})
    forms = facts_check.load_project(tmp_path).runner_forms
    fault = facts_check.selector_fault(VITEST, tmp_path, runner_forms=forms, fact_id="APP-001")
    assert fault == "tests/contracts/a.test.ts does not exist"


@pytest.mark.parametrize(
    "check",
    [
        VITEST + " --reporter=json",
        'pnpm exec vitest run tests/contracts/a.test.ts -t "APP-001" ; true',
        'pnpm exec vitest run tests/contracts/a.test.ts tests/b.test.ts -t "APP-001"',
        "pnpm exec vitest run tests/contracts/a.test.ts",
    ],
)
def test_a_check_outside_the_declared_form_is_a_fault(tmp_path: Path, check: str) -> None:
    _project(tmp_path, VITEST, TESTS)
    forms = facts_check.load_project(tmp_path).runner_forms
    fault = facts_check.selector_fault(check, tmp_path, runner_forms=forms, fact_id="APP-001")
    assert fault == f"a token outside the check's form in {check!r}"


def test_a_fault_is_reported_in_every_mode(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, {"tests/contracts/a.test.ts": "// none\n"})
    code, out = _gate(tmp_path, capsys, "--orphans")
    assert code == 1
    assert "ambiguous checks: APP-001" in out


def test_the_other_runner_s_form_does_not_accept_the_check(tmp_path: Path) -> None:
    _project(tmp_path, VITEST, TESTS, toml='[facts.check_forms]\nplaywright = ["x"]\n')
    forms = facts_check.load_project(tmp_path).runner_forms
    assert facts_check.selector_fault(VITEST, tmp_path, runner_forms=forms, fact_id="APP-001")


def test_a_vitest_report_never_satisfies_a_pytest_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, VITEST, TESTS)
    _report(tmp_path, {"tests/t.py::a": {"title": "APP-001 x", "outcome": "passed"}})
    assert _gate(tmp_path, capsys)[0] == 1
