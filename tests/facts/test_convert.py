"""The converters: each runner's raw report to the normalized format `load_reports` reads."""

import json
from pathlib import Path

import pytest

from claude_plugins_tools.__main__ import build_parser
from claude_plugins_tools.__main__ import main as cpt
from claude_plugins_tools.facts import convert
from claude_plugins_tools.facts.reports import Entry, load_reports

FIXTURES = Path(__file__).parent / "fixtures"
# vitest names its files by absolute path; the fixtures were run in /repo/app.
REPO = Path("/repo")


def _load(tmp_path: Path, out: Path) -> dict[str, Entry]:
    """Round trip: what `load_reports` reads from the converter's file."""
    (report,) = load_reports(out.parent).values()
    return report


# --- vitest -------------------------------------------------------------------------


@pytest.mark.parametrize("fixture", ["vitest4.json", "vitest5.json"])
def test_vitest_outcomes_ids_and_repo_relative_files(fixture: str) -> None:
    raw = json.loads((FIXTURES / fixture).read_text(encoding="utf-8"))
    entries = convert.from_vitest(raw, root="app", repo=REPO)
    file = "app/src/math.test.ts"
    assert entries == {
        f"{file}::math > add > ZZZ-001 adds": {
            "title": "ZZZ-001 adds",
            "outcome": "passed",
            "file": file,
        },
        f"{file}::math > add > ZZZ-002 fails": {
            "title": "ZZZ-002 fails",
            "outcome": "failed",
            "file": file,
        },
        f"{file}::math > ZZZ-003 skipped": {
            "title": "ZZZ-003 skipped",
            "outcome": "skipped",
            "file": file,
        },
        f"{file}::math > ZZZ-004 todo": {
            "title": "ZZZ-004 todo",
            "outcome": "skipped",
            "file": file,
        },
        f"{file}::top level": {"title": "top level", "outcome": "passed", "file": file},
    }


def test_vitest_without_root_is_relative_to_the_repository() -> None:
    raw = json.loads((FIXTURES / "vitest4.json").read_text(encoding="utf-8"))
    assert {e["file"] for e in convert.from_vitest(raw, root="", repo=REPO).values()} == {
        "app/src/math.test.ts"
    }


def test_vitest_root_is_where_vitest_ran_so_a_name_outside_it_is_refused() -> None:
    raw = json.loads((FIXTURES / "vitest4.json").read_text(encoding="utf-8"))
    with pytest.raises(convert.ConvertError, match="outside"):
        convert.from_vitest(raw, root="other", repo=REPO)


def test_vitest_relative_name_is_taken_relative_to_root() -> None:
    raw = {
        "testResults": [
            {
                "name": "src/a.test.ts",
                "assertionResults": [{"ancestorTitles": [], "title": "t", "status": "passed"}],
            }
        ]
    }
    entries = convert.from_vitest(raw, root="app", repo=REPO)
    assert entries == {
        "app/src/a.test.ts::t": {"title": "t", "outcome": "passed", "file": "app/src/a.test.ts"}
    }


def test_vitest_the_worse_outcome_wins_on_a_duplicate_id() -> None:
    def case(status: str) -> dict:
        return {"ancestorTitles": ["d"], "title": "t", "status": status}

    raw = {
        "testResults": [
            {
                "name": "/repo/a.test.ts",
                "assertionResults": [case("passed"), case("failed"), case("skipped")],
            }
        ]
    }
    assert convert.from_vitest(raw, root="", repo=REPO)["a.test.ts::d > t"]["outcome"] == "failed"
    raw["testResults"][0]["assertionResults"] = [case("skipped"), case("passed")]
    assert convert.from_vitest(raw, root="", repo=REPO)["a.test.ts::d > t"]["outcome"] == "skipped"


def test_vitest_round_trip_through_load_reports(tmp_path: Path) -> None:
    out = tmp_path / "vitest.json"
    assert convert.convert("vitest", FIXTURES / "vitest5.json", out, root="app", repo=REPO) == out
    report = _load(tmp_path, out)
    entry = report["app/src/math.test.ts::math > add > ZZZ-001 adds"]
    assert entry == Entry(
        "app/src/math.test.ts::math > add > ZZZ-001 adds",
        "ZZZ-001 adds",
        "passed",
        "app/src/math.test.ts",
        None,
    )
    assert len(report) == 5


# --- playwright ---------------------------------------------------------------------


def test_playwright_outcomes_and_test_dir_prefix() -> None:
    raw = json.loads((FIXTURES / "playwright.json").read_text(encoding="utf-8"))
    entries = convert.from_playwright(raw, test_dir="tests/e2e")
    a, b = "tests/e2e/a.spec.ts", "tests/e2e/sub/b.spec.ts"
    assert {key: (v["title"], v["outcome"], v["file"]) for key, v in entries.items()} == {
        f"{a}::ZZZ-013 flaky": ("ZZZ-013 flaky", "failed", a),
        f"{a}::group > ZZZ-010 passes": ("ZZZ-010 passes", "passed", a),
        f"{a}::group > ZZZ-011 fails": ("ZZZ-011 fails", "failed", a),
        f"{a}::group > ZZZ-012 skipped": ("ZZZ-012 skipped", "skipped", a),
        f"{b}::ZZZ-014 in subdir": ("ZZZ-014 in subdir", "passed", b),
    }


def test_playwright_without_test_dir_keeps_the_file_as_reported() -> None:
    raw = json.loads((FIXTURES / "playwright.json").read_text(encoding="utf-8"))
    files = {e["file"] for e in convert.from_playwright(raw, test_dir="").values()}
    assert files == {"a.spec.ts", "sub/b.spec.ts"}
    files = {e["file"] for e in convert.from_playwright(raw, test_dir="tests/e2e/").values()}
    assert files == {"tests/e2e/a.spec.ts", "tests/e2e/sub/b.spec.ts"}


def test_playwright_one_test_per_project_keeps_the_worst() -> None:
    spec = {
        "title": "t",
        "file": "a.spec.ts",
        "tests": [{"status": "expected"}, {"status": "unexpected"}, {"status": "skipped"}],
    }
    raw = {"suites": [{"title": "a.spec.ts", "specs": [spec]}]}
    assert convert.from_playwright(raw, test_dir="e2e")["e2e/a.spec.ts::t"]["outcome"] == "failed"


def test_playwright_round_trip_through_load_reports(tmp_path: Path) -> None:
    out = tmp_path / "e2e.json"
    convert.convert("playwright", FIXTURES / "playwright.json", out, test_dir="tests/e2e")
    report = _load(tmp_path, out)
    assert report["tests/e2e/a.spec.ts::group > ZZZ-010 passes"] == Entry(
        "tests/e2e/a.spec.ts::group > ZZZ-010 passes",
        "ZZZ-010 passes",
        "passed",
        "tests/e2e/a.spec.ts",
        None,
    )
    assert len(report) == 5


# --- nextest ------------------------------------------------------------------------


def test_nextest_binary_ids_outcomes_and_ignored_absent() -> None:
    entries = convert.from_nextest((FIXTURES / "nextest.xml").read_text(encoding="utf-8"))
    assert entries == {
        "demo::tests::adds": {"title": "tests::adds", "outcome": "passed", "binary": "demo"},
        "demo::tests::fails": {"title": "tests::fails", "outcome": "failed", "binary": "demo"},
        "demo::api::works": {"title": "works", "outcome": "passed", "binary": "demo::api"},
    }
    assert not any("slow" in key for key in entries)  # the #[ignore]d test


def test_nextest_skipped_cases_are_not_entries_and_flaky_is_failed() -> None:
    xml = """<testsuites><testsuite name="p::b">
      <testcase name="ignored" classname="p::b"><skipped/></testcase>
      <testcase name="flaky" classname="p::b"><flakyFailure message="m"/></testcase>
      <testcase name="flakyerr" classname="p::b"><flakyError message="m"/></testcase>
      <testcase name="broken" classname="p::b"><error message="m"/></testcase>
      <testcase name="retried" classname="p::b"><failure message="m"/><rerunFailure/></testcase>
      <testcase name="dup" classname="p::b"/>
      <testcase name="dup" classname="p::b"><failure message="m"/></testcase>
    </testsuite></testsuites>"""
    outcomes = {key: e["outcome"] for key, e in convert.from_nextest(xml).items()}
    assert outcomes == {
        "p::b::flaky": "failed",
        "p::b::flakyerr": "failed",
        "p::b::broken": "failed",
        "p::b::retried": "failed",
        "p::b::dup": "failed",
    }


def test_nextest_round_trip_through_load_reports(tmp_path: Path) -> None:
    out = tmp_path / "rust.json"
    convert.convert("nextest", FIXTURES / "nextest.xml", out)
    report = _load(tmp_path, out)
    assert report["demo::api::works"] == Entry(
        "demo::api::works", "works", "passed", None, "demo::api"
    )
    assert report["demo::tests::fails"].outcome == "failed"
    assert len(report) == 3


# --- the command line ---------------------------------------------------------------


def test_cli_converts_each_runner(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "out"
    for argv in (
        [
            "vitest",
            str(FIXTURES / "vitest4.json"),
            str(out / "v.json"),
            "--root",
            "app",
            "--repo",
            "/repo",
        ],
        [
            "playwright",
            str(FIXTURES / "playwright.json"),
            str(out / "p.json"),
            "--test-dir",
            "tests/e2e",
        ],
        ["nextest", str(FIXTURES / "nextest.xml"), str(out / "n.json")],
    ):
        assert cpt(["facts", "report", *argv]) == 0
    assert set(load_reports(out)) == {"v", "p", "n"}


def test_cli_unreadable_input_is_an_error_not_an_empty_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    out = tmp_path / "out.json"
    assert cpt(["facts", "report", "vitest", str(bad), str(out)]) == 1
    assert cpt(["facts", "report", "nextest", str(tmp_path / "missing.xml"), str(out)]) == 1
    assert cpt(["facts", "report", "playwright", str(bad), str(out)]) == 1
    assert not out.exists()
    assert "bad.json" in capsys.readouterr().err


def test_old_facts_invocations_still_parse(tmp_path: Path) -> None:
    parser = build_parser()
    args = parser.parse_args(["facts", "--orphans"])
    assert args.orphans is True
    assert args.facts_command is None
    args = parser.parse_args(["facts", "--reports", str(tmp_path), "--implemented"])
    assert args.reports == tmp_path
    assert args.implemented is True
    assert args.facts_command is None


def test_vitest_names_under_a_symlinked_checkout_are_resolved(tmp_path: Path) -> None:
    real = tmp_path / "real"
    (real / "app" / "src").mkdir(parents=True)
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    raw = {
        "testResults": [
            {
                "name": str(link / "app" / "src" / "a.test.ts"),  # vitest ran under the link
                "assertionResults": [
                    {"ancestorTitles": [], "title": "ZZZ-001 x", "status": "passed"}
                ],
            }
        ]
    }
    entries = convert.from_vitest(raw, "app", real)
    assert [e["file"] for e in entries.values()] == ["app/src/a.test.ts"]
    outside = {"testResults": [{**raw["testResults"][0], "name": str(tmp_path / "x.test.ts")}]}
    with pytest.raises(convert.ConvertError):
        convert.from_vitest(outside, "app", real)
