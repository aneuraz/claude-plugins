"""`--exclude-requires`, `--vitest-root`, `--root` and the `cpt facts` dispatch."""

from pathlib import Path

import pytest
import yaml

from claude_plugins_tools import __main__ as cpt
from claude_plugins_tools.facts import check as facts_check

PLAIN = "uv run --all-packages --exact pytest tests/t.py::a -v"
MARKED = "uv run --all-packages --exact pytest -m integration tests/t.py::b -v"


def _project(root: Path, facts: list[dict[str, object]]) -> None:
    specs = root / "docs" / "superpowers" / "specs"
    specs.mkdir(parents=True)
    ids = " ".join(str(fact["id"]) for fact in facts)
    (specs / "x-design.md").write_text(ids + "\n", encoding="utf-8")
    (specs / "x-facts.md").write_text(yaml.safe_dump(facts), encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "t.py").write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")


def _fact(fact_id: str, check: str, **extra: object) -> dict[str, object]:
    return {"id": fact_id, "status": "@implemented", "statement": "s", "check": check} | extra


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    checks: list[str] = []
    monkeypatch.setattr(facts_check, "run_check", lambda check, _root: checks.append(check) or True)
    return checks


def test_an_excluded_requirement_is_listed_and_not_run(
    tmp_path: Path, ran: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    _project(
        tmp_path, [_fact("AAA-001", PLAIN), _fact("AAA-002", MARKED, requires=["integration"])]
    )
    assert facts_check.main(["--exclude-requires", "integration,x", "--root", str(tmp_path)]) == 0
    assert ran == [PLAIN]
    assert "- not run: AAA-002 (requires: integration)" in capsys.readouterr().out


def test_without_the_flag_every_fact_runs(tmp_path: Path, ran: list[str]) -> None:
    _project(
        tmp_path, [_fact("AAA-001", PLAIN), _fact("AAA-002", MARKED, requires=["integration"])]
    )
    assert facts_check.main(["--root", str(tmp_path)]) == 0
    assert ran == [PLAIN, MARKED]


def test_a_marker_without_requires_is_valid_unless_the_flag_is_given(
    tmp_path: Path, ran: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    """A candle fact using `-m integration` without `requires` stays valid."""
    _project(tmp_path, [_fact("AAA-001", MARKED)])
    assert facts_check.main(["--root", str(tmp_path)]) == 0
    assert facts_check.main(["--orphans", "--root", str(tmp_path)]) == 0
    capsys.readouterr()
    assert facts_check.main(["--exclude-requires", "net", "--root", str(tmp_path)]) == 1
    assert "requires [] but the check selects ['integration']" in capsys.readouterr().out


def test_requires_fault_compares_markers_to_requirements() -> None:
    fact = _fact("AAA-001", "uv run pytest tests/t.py::a -m net", requires=["net"])
    assert facts_check.requires_fault(fact) is None
    assert facts_check.requires_fault({**fact, "requires": ["db"]}) == (
        "requires ['db'] but the check selects ['net']"
    )
    assert facts_check.requires_fault(_fact("AAA-002", PLAIN)) is None
    assert facts_check.requires_fault(_fact("AAA-003", PLAIN, requires=["net"])) is not None


def test_exclude_requires_lists_the_fact_as_not_run_with_reports(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, [_fact("AAA-001", MARKED, requires=["integration"])])
    reports = tmp_path / "reports"
    reports.mkdir()
    argv = ["--exclude-requires", "integration", "--reports", str(reports)]
    assert facts_check.main([*argv, "--root", str(tmp_path)]) == 0
    assert "not run (requires: integration)" in capsys.readouterr().out


def test_orphans_ignores_implemented_and_runs_nothing(tmp_path: Path, ran: list[str]) -> None:
    _project(tmp_path, [_fact("AAA-001", PLAIN)])
    assert facts_check.main(["--orphans", "--implemented", "--root", str(tmp_path)]) == 0
    assert ran == []


def test_the_vitest_root_is_a_parameter(tmp_path: Path) -> None:
    test = tmp_path / "web" / "tests" / "x.test.ts"
    test.parent.mkdir(parents=True)
    test.write_text('it("APP-001 does it", () => {});\n', encoding="utf-8")
    check = 'pnpm -C agent exec vitest run tests/x.test.ts -t "APP-001"'
    assert facts_check.selector_fault(check, tmp_path, "web") is None
    assert facts_check.selector_fault(check, tmp_path) == "agent/tests/x.test.ts does not exist"


def test_root_defaults_to_the_current_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, ran: list[str]
) -> None:
    _project(tmp_path, [_fact("AAA-001", PLAIN)])
    monkeypatch.chdir(tmp_path)
    assert facts_check.main(["--orphans"]) == 0


def test_a_project_without_fact_sets_passes(tmp_path: Path) -> None:
    assert facts_check.main(["--orphans", "--root", str(tmp_path)]) == 0


def test_cpt_dispatches_facts_and_rejects_the_rest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, [_fact("AAA-001", PLAIN)])
    assert cpt.main(["facts", "--orphans", "--root", str(tmp_path)]) == 0
    assert "✓ no orphan fact" in capsys.readouterr().out
    assert cpt.main([]) == 2
    with pytest.raises(SystemExit) as exit_info:
        cpt.main(["wiki"])
    assert exit_info.value.code == 2


def test_cpt_facts_audits_the_forms_of_project_toml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    outside = "uv run --all-packages --exact pytest tests/t.py::a -v -k x"
    _project(tmp_path, [_fact("AAA-001", outside)])
    # no .claude/project.toml: no form audit
    assert cpt.main(["facts", "--orphans", "--root", str(tmp_path)]) == 0
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "project.toml").write_text(
        '[facts]\ncheck_forms = ["uv run --all-packages --exact pytest -v"]\n', encoding="utf-8"
    )
    capsys.readouterr()
    assert cpt.main(["facts", "--orphans", "--root", str(tmp_path)]) == 1
    assert "a token outside the check's form" in capsys.readouterr().out


def test_cpt_facts_refuses_a_malformed_project_toml(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, [_fact("AAA-001", PLAIN)])
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "project.toml").write_text(
        '[facts]\ncheck_forms = "uv run pytest"\n', encoding="utf-8"
    )
    assert cpt.main(["facts", "--orphans", "--root", str(tmp_path)]) == 1
    assert "facts.check_forms" in capsys.readouterr().err


def test_cpt_help_says_usage_once(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        cpt.main(["--help"])
    assert stopped.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("usage: cpt {facts,wiki} ...\n")
    assert "usage: usage:" not in out


def test_cpt_without_a_command_prints_its_usage(capsys: pytest.CaptureFixture[str]) -> None:
    assert cpt.main([]) == 2
    assert capsys.readouterr().err == "usage: cpt {facts,wiki} ...\n"
