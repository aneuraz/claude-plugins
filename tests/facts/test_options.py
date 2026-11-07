"""The facts options: whole-file vitest, --exclude-requires with reports, --only, --owner,
`orphans = "facts-lines"`, `schema`, and the pending list. Checks and spec lines are copied
from `capture`, the first repository to use them."""

import json
from pathlib import Path

import pytest
import yaml

from claude_plugins_tools.facts import check as facts_check
from claude_plugins_tools.facts import orphans

SPECS = Path("docs") / "superpowers" / "specs"
FILES_FORM = "[facts.check_forms]\nvitest-files = ['npm --prefix app test -- <files>']\n"
UI_007_VITEST = "npm --prefix app test -- src/App.test.ts"
# capture's UI-002 and CPT-004 as written today: shell checks, not selectors.
UI_002_LITERAL = (
    '[ "$(rm -f /tmp/ui-002.json; npm --prefix app test -- --reporter=json '
    '--outputFile=/tmp/ui-002.json -t "carries no excerpt" >/dev/null 2>&1; python3 -c '
    "\"import json;d=json.load(open('/tmp/ui-002.json'));print(d['numPassedTests'] "
    "if d['success'] and d['numFailedTests']==0 else 0)\" 2>/dev/null)\" = 2 ]"
)
CPT_004_LITERAL = UI_002_LITERAL.replace("ui-002", "cpt-004").replace(
    '-t "carries no excerpt"', "src/citation/remove.test.ts"
)


def _fact(fact_id: str, check: str | None, status: str = "@implemented", **extra: object) -> dict:
    fact = {"id": fact_id, "status": status, "statement": "s"} | extra
    return fact if check is None else fact | {"check": check}


def _project(
    root: Path,
    facts: list[dict],
    toml: str = "",
    design: str | None = None,
    files: tuple[str, ...] = (),
) -> None:
    specs = root / SPECS
    specs.mkdir(parents=True, exist_ok=True)
    ids = " ".join(str(fact["id"]) for fact in facts)
    (specs / "x-design.md").write_text(ids + "\n" if design is None else design, encoding="utf-8")
    (specs / "x-facts.md").write_text(yaml.safe_dump(facts), encoding="utf-8")
    (root / ".claude").mkdir(exist_ok=True)
    (root / ".claude" / "project.toml").write_text(toml, encoding="utf-8")
    for file in files:
        (root / file).parent.mkdir(parents=True, exist_ok=True)
        (root / file).write_text("", encoding="utf-8")


def _entry(file: str, title: str, outcome: str = "passed", ancestors: tuple[str, ...] = ()):
    return {
        "id": " > ".join([*ancestors, title]),
        "value": {"title": title, "outcome": outcome, "file": file},
        "file": file,
        "ancestors": ancestors,
    }


def _report(root: Path, entries: list[dict], job: str = "ui") -> Path:
    path = root / "reports" / f"{job}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {f"{e['file']}::{e['id']}": e["value"] for e in entries}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path.parent


def _gate(root: Path, *argv: str) -> int:
    return facts_check.main(["--root", str(root), *argv])


@pytest.fixture
def ran(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    checks: list[str] = []
    monkeypatch.setattr(facts_check, "run_check", lambda check, _root: checks.append(check) or True)
    return checks


# ---- whole-file vitest ------------------------------------------------------------


def test_a_whole_file_check_is_green_when_every_entry_of_its_file_passed(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, [_fact("UI-007", UI_007_VITEST)], FILES_FORM, files=("app/src/App.test.ts",))
    reports = _report(
        tmp_path,
        [
            _entry("app/src/App.test.ts", "renders"),
            _entry("app/src/App.test.ts", "opens", ancestors=("App",)),
            # the same relative path outside the prefix directory is another file
            _entry("src/App.test.ts", "elsewhere", "failed"),
        ],
    )
    assert _gate(tmp_path, "--reports", str(reports)) == 0
    assert "✓ UI-007" in capsys.readouterr().out


def test_a_failed_skipped_or_missing_entry_is_not_green(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _project(tmp_path, [_fact("UI-007", UI_007_VITEST)], FILES_FORM, files=("app/src/App.test.ts",))
    for entries, reason in (
        (
            [_entry("app/src/App.test.ts", "a"), _entry("app/src/App.test.ts", "b", "failed")],
            "failed",
        ),
        ([_entry("app/src/App.test.ts", "a", "skipped")], "skipped"),
        ([_entry("app/src/Other.test.ts", "a")], "not run"),
    ):
        reports = _report(tmp_path, entries)
        assert _gate(tmp_path, "--reports", str(reports)) == 1
        assert reason in capsys.readouterr().out


def test_no_report_at_all_reads_not_run(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _project(tmp_path, [_fact("UI-007", UI_007_VITEST)], FILES_FORM, files=("app/src/App.test.ts",))
    assert _gate(tmp_path, "--reports", str(tmp_path / "none")) == 1
    assert "not run" in capsys.readouterr().out


def test_several_files_and_a_directory_select_their_entries(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # capture's CPT-003 and UI-005 name a directory and several files.
    check = "npm --prefix app test -- src/concept src/note/Promote.test.ts"
    files = (
        "app/src/concept/a.test.ts",
        "app/src/note/Promote.test.ts",
        "app/src/note/Other.test.ts",
    )
    _project(tmp_path, [_fact("CPT-003", check)], FILES_FORM, files=files)
    entries = [
        _entry("app/src/concept/a.test.ts", "x"),
        _entry("app/src/note/Promote.test.ts", "y"),
        _entry("app/src/note/Other.test.ts", "z", "failed"),  # not named
        _entry("app/src/conceptual/b.test.ts", "w", "failed"),  # a sibling, not a child
    ]
    assert _gate(tmp_path, "--reports", str(_report(tmp_path, entries))) == 0
    capsys.readouterr()
    entries[0] = _entry("app/src/concept/a.test.ts", "x", "failed")
    assert _gate(tmp_path, "--reports", str(_report(tmp_path, entries))) == 1


def test_dash_t_is_a_regex_over_the_full_name_as_vitest_joins_it(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # vitest: getTaskFullName joins ancestor titles and the title with a space, and
    # interpretTaskModes keeps a test when the name matches the regex (unanchored).
    check = f'{UI_007_VITEST} -t "^Palette (opens|closes) "'
    _project(tmp_path, [_fact("UI-003", check)], FILES_FORM, files=("app/src/App.test.ts",))
    f = "app/src/App.test.ts"
    entries = [
        _entry(f, "opens on key", ancestors=("Palette",)),
        _entry(f, "closes on escape", ancestors=("Palette",)),
        _entry(f, "unrelated", "failed", ancestors=("Palette",)),
        _entry(f, "opens elsewhere", "failed", ancestors=("Other",)),
    ]
    assert _gate(tmp_path, "--reports", str(_report(tmp_path, entries))) == 0
    capsys.readouterr()
    entries[1] = _entry(f, "closes on escape", "failed", ancestors=("Palette",))
    assert _gate(tmp_path, "--reports", str(_report(tmp_path, entries))) == 1


def test_a_pattern_that_selects_nothing_reads_not_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    check = f'{UI_007_VITEST} -t "carries no excerpt"'
    _project(tmp_path, [_fact("UI-002", check)], FILES_FORM, files=("app/src/App.test.ts",))
    reports = _report(tmp_path, [_entry("app/src/App.test.ts", "something else")])
    assert _gate(tmp_path, "--reports", str(reports)) == 1
    assert "not run" in capsys.readouterr().out


@pytest.mark.parametrize(
    ("check", "fault"),
    [
        (UI_002_LITERAL, "unknown runner"),  # capture's UI-002 today
        (CPT_004_LITERAL, "unknown runner"),
        ('npm --prefix app test -- -t "carries no excerpt"', "names no test file"),
        ("npm --prefix app test --", "names no test file"),
        ("npm --prefix app test -- --reporter=json src/App.test.ts", "names no test file"),
        ("npm --prefix app test -- src/App.test.ts --coverage", "a token outside"),
        ("npm --prefix app test -- src/Gone.test.ts", "does not exist"),
        ('npm --prefix app test -- src/App.test.ts -t "(open"', "not a regular expression"),
    ],
)
def test_a_check_outside_the_whole_file_form_is_a_fault(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], check: str, fault: str
) -> None:
    _project(tmp_path, [_fact("UI-002", check)], FILES_FORM, files=("app/src/App.test.ts",))
    for mode in (["--orphans"], ["--reports", str(tmp_path / "reports")]):
        assert _gate(tmp_path, *mode) == 1
        assert fault in capsys.readouterr().out


def test_the_form_is_the_projects_own_prefix(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    toml = "[facts.check_forms]\nvitest-files = ['pnpm --dir web exec vitest run <files>']\n"
    check = "pnpm --dir web exec vitest run tests/a.test.ts"
    _project(tmp_path, [_fact("WEB-001", check)], toml, files=("web/tests/a.test.ts",))
    reports = _report(tmp_path, [_entry("web/tests/a.test.ts", "ok")])
    assert _gate(tmp_path, "--reports", str(reports)) == 0
    # the capture form is not this project's
    other = _fact("WEB-001", "npm --prefix app test -- tests/a.test.ts")
    _project(tmp_path, [other], toml, files=("web/tests/a.test.ts",))
    assert _gate(tmp_path, "--orphans") == 1
    assert "unknown runner" in capsys.readouterr().out


# ---- --exclude-requires with reports ----------------------------------------------

PLAIN = "uv run --all-packages --exact pytest tests/t.py::a -v"
MARKED = "uv run --all-packages --exact pytest -m parhaf tests/t.py::b -v"


def _pytest_project(root: Path, facts: list[dict], toml: str = "") -> Path:
    _project(root, facts, toml, files=("tests/t.py",))
    (root / "tests" / "t.py").write_text("def a(): pass\ndef b(): pass\n", encoding="utf-8")
    reports = root / "reports"
    reports.mkdir()
    (reports / "job.json").write_text('{"tests/t.py::a": "passed"}', encoding="utf-8")
    return reports


def test_an_excluded_requirement_is_not_run_and_not_red_with_reports(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    facts = [_fact("AAA-001", PLAIN), _fact("AAA-002", MARKED, requires=["parhaf"])]
    reports = _pytest_project(tmp_path, facts)
    assert _gate(tmp_path, "--reports", str(reports)) == 1  # AAA-002 has no report
    capsys.readouterr()
    assert _gate(tmp_path, "--reports", str(reports), "--exclude-requires", "parhaf,baseline") == 0
    out = capsys.readouterr().out
    assert "✓ AAA-001" in out
    assert "AAA-002" in out
    assert "not run (requires: parhaf)" in out
    assert "red facts" not in out


def test_the_markers_audit_runs_with_reports_when_the_flag_is_given(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    reports = _pytest_project(tmp_path, [_fact("AAA-001", MARKED)])
    (reports / "job.json").write_text('{"tests/t.py::b": "passed"}', encoding="utf-8")
    assert _gate(tmp_path, "--reports", str(reports)) == 0
    capsys.readouterr()
    assert _gate(tmp_path, "--reports", str(reports), "--exclude-requires", "net") == 1
    assert "requires [] but the check selects ['parhaf']" in capsys.readouterr().out


# ---- --only and --owner -----------------------------------------------------------


def test_only_is_repeatable_and_runs_just_those_facts(tmp_path: Path, ran: list[str]) -> None:
    facts = [_fact(f"AAA-00{n}", PLAIN) for n in (1, 2, 3)]
    _pytest_project(tmp_path, facts)
    assert _gate(tmp_path, "--only", "AAA-001", "--only", "AAA-003") == 0
    assert ran == [PLAIN, PLAIN]


def test_an_unknown_only_id_is_an_error_that_names_it(
    tmp_path: Path, ran: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    _pytest_project(tmp_path, [_fact("AAA-001", PLAIN)])
    assert _gate(tmp_path, "--only", "AAA-001", "--only", "ZZZ-009") != 0
    captured = capsys.readouterr()
    assert "ZZZ-009" in captured.out + captured.err
    assert ran == []


OWNER = "[facts]\nowner = true\n"


def test_owner_keeps_the_facts_of_that_owner(tmp_path: Path, ran: list[str]) -> None:
    facts = [_fact("AAA-001", PLAIN, owner="core"), _fact("AAA-002", PLAIN, owner="agent")]
    _pytest_project(tmp_path, facts, OWNER)
    assert _gate(tmp_path, "--owner", "agent") == 0
    assert len(ran) == 1


def test_owner_is_an_error_unless_the_project_declares_it(
    tmp_path: Path, ran: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    _pytest_project(tmp_path, [_fact("AAA-001", PLAIN, owner="core")])
    assert _gate(tmp_path, "--owner", "core") != 0
    captured = capsys.readouterr()
    assert "owner = true" in captured.out + captured.err
    assert ran == []


def test_owner_with_reports_judges_only_that_owner(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    facts = [_fact("AAA-001", PLAIN, owner="core"), _fact("AAA-002", MARKED, owner="agent")]
    reports = _pytest_project(tmp_path, facts, OWNER)
    assert _gate(tmp_path, "--reports", str(reports), "--owner", "core") == 0
    assert "AAA-002" not in capsys.readouterr().out


# ---- orphans = "facts-lines" ------------------------------------------------------

# Lines copied from capture's specs.
LINES = """\
## Section
*Facts : SPL-001 à SPL-007 (atomicité), CLI-005 (une entrée ingérée), SPL-011 (aucune perte).*
*Facts : I18N-001 (aucune chaîne en dur), I18N-004 (l'agent Swift cite une clé), QRY-003 (repli).*
*Facts : OCR-007a, OCR-007b, OCR-007c, OCR-007d.*
**Facts :** CLI-001 to CLI-003, **PRJ-008**.
The prose names SEC-009 but is not a Facts line.
"""


def test_ids_cited_on_facts_lines(tmp_path: Path) -> None:
    (tmp_path / "a-design.md").write_text(LINES, encoding="utf-8")
    (tmp_path / "a-facts.md").write_text("*Facts : FCT-001.*", encoding="utf-8")  # not a spec
    cited = orphans.cited_ids(tmp_path)
    assert "FCT-001" not in cited
    assert {f"SPL-{n:03d}" for n in range(1, 8)} <= cited
    assert {"I18N-001", "I18N-004", "OCR-007a", "OCR-007d", "PRJ-008"} <= cited
    assert {"CLI-001", "CLI-002", "CLI-003"} <= cited
    assert "SEC-009" not in cited
    assert "OCR-007" not in cited
    assert orphans.ids_cited_in("*Facts : none — this section is prose.*") == set()


def test_facts_lines_orphans_and_dangling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    toml = '[facts]\norphans = "facts-lines"\n'
    facts = [_fact(i, PLAIN) for i in ("SPL-001", "SPL-002", "OCR-007a", "I18N-004", "STO-099")]
    _pytest_project(tmp_path, facts, toml)
    spec = "*Facts : SPL-001 à SPL-002, OCR-007a, I18N-004, SPL-003, OCR-007b.*\n"
    (tmp_path / SPECS / "phase-3-design.md").write_text(spec, encoding="utf-8")
    assert _gate(tmp_path, "--orphans") == 1
    out = capsys.readouterr().out
    assert "orphan facts" in out
    assert "STO-099" in out
    assert "dangling" in out
    assert "SPL-003" in out
    assert "OCR-007b" in out
    assert "SPL-001" not in out.split("dangling")[1]


def test_facts_lines_clean_and_independent_of_the_sibling_design(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    toml = '[facts]\norphans = "facts-lines"\n'
    _pytest_project(tmp_path, [_fact("SPL-001", PLAIN)], toml)
    (tmp_path / SPECS / "x-design.md").write_text("SPL-001 only in prose\n", encoding="utf-8")
    assert _gate(tmp_path, "--orphans") == 1  # prose does not count
    capsys.readouterr()
    (tmp_path / SPECS / "y.md").write_text("*Facts : SPL-001.*\n", encoding="utf-8")
    assert _gate(tmp_path, "--orphans") == 0
    assert "✗" not in capsys.readouterr().out


def test_design_text_stays_the_default(tmp_path: Path) -> None:
    _pytest_project(tmp_path, [_fact("SPL-001", PLAIN)])
    assert _gate(tmp_path, "--orphans") == 0


# ---- schema -----------------------------------------------------------------------

# The lists of capture's scripts/facts_check.py.
SCHEMA = """\
[facts.schema]
allowed = ["id", "status", "level", "statement", "check", "source", "owner", "blocker", "timeout"]
required = ["id", "status", "level", "statement", "source", "owner"]
statuses = ["@draft", "@spec", "@implemented"]
"""


def _full(fact_id: str, **extra: object) -> dict:
    base = {"level": "unit", "source": "spec", "owner": "core", "check": PLAIN}
    return {"id": fact_id, "status": "@implemented", "statement": "s"} | base | extra


def test_a_conforming_fact_set_passes_and_timeout_is_ignored(
    tmp_path: Path, ran: list[str]
) -> None:
    _pytest_project(tmp_path, [_full("AAA-001", timeout=600)], SCHEMA)
    assert _gate(tmp_path) == 0
    assert ran == [PLAIN]


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        ({"colour": "red"}, "colour"),
        ({"status": "@wip"}, "@wip"),
        ({"owner": None}, "owner"),
    ],
)
def test_schema_faults(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], extra: dict, message: str
) -> None:
    fact = _full("AAA-001", **extra)
    if extra == {"owner": None}:
        del fact["owner"]
    _pytest_project(tmp_path, [fact], SCHEMA)
    assert _gate(tmp_path, "--orphans") == 1
    out = capsys.readouterr().out
    assert "schema" in out
    assert message in out


def test_an_implemented_fact_without_a_check_is_a_fault(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fact = _full("AAA-001")
    del fact["check"]
    spec = _full("AAA-002", status="@spec")
    del spec["check"]
    _pytest_project(tmp_path, [fact, spec], SCHEMA)
    assert _gate(tmp_path, "--orphans") == 1
    out = capsys.readouterr().out
    assert "AAA-001: @implemented without a check" in out
    assert "AAA-002" not in out


def test_a_duplicate_id_is_a_fault(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _pytest_project(tmp_path, [_full("AAA-001"), _full("AAA-001")], SCHEMA)
    assert _gate(tmp_path, "--orphans") == 1
    assert "AAA-001: duplicate id" in capsys.readouterr().out


def test_without_a_schema_nothing_is_checked(tmp_path: Path) -> None:
    _pytest_project(tmp_path, [_fact("AAA-001", PLAIN, colour="red")])
    assert _gate(tmp_path, "--orphans") == 0


# ---- pending ----------------------------------------------------------------------


def test_implemented_lists_the_facts_not_judged_as_pending(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    facts = [
        _fact("AAA-001", PLAIN),
        _fact("AAA-002", "uv run pytest tests/t.py::b", "@spec"),
        _fact("AAA-003", "uv run pytest tests/t.py::b", "@draft"),
    ]
    reports = _pytest_project(tmp_path, facts)
    assert _gate(tmp_path, "--reports", str(reports), "--implemented") == 0
    out = capsys.readouterr().out
    assert "pending: AAA-002 [@spec]" in out
    assert "pending: AAA-003 [@draft]" in out
    assert "pending: AAA-001" not in out
    _gate(tmp_path, "--reports", str(reports))
    assert "pending" not in capsys.readouterr().out
