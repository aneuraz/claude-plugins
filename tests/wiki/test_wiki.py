"""The wiki tool, ported from candle's tests/contracts/test_wiki.py at 275bce0.

Fixture repositories come from tests/wiki/helpers.py; their `.claude/project.toml` sends issue
references to aneuraz/candle-legacy, as candle's hard-coded rule 7 did.
"""

from collections.abc import Mapping
from pathlib import Path

import pytest

from claude_plugins_tools.__main__ import main
from claude_plugins_tools.packs import Pack, load_packs
from claude_plugins_tools.project import load_project
from claude_plugins_tools.wiki.anchors import Anchors, github_anchor
from claude_plugins_tools.wiki.check import RULES, Fault, check, lint
from claude_plugins_tools.wiki.index import render_index
from tests.wiki.helpers import PROJECT, clean_wiki, rule, write, write_pack
from tests.wiki.helpers import commit as fixture_commit


def test_anchors_match_github_on_known_headings() -> None:
    # Read from GitHub's rendering of candle's docs/doctrine.md on 2026-10-12.
    assert github_anchor(
        "4. `indeterminate` exists so that a failure does not look like a judgement"
    ) == ("4-indeterminate-exists-so-that-a-failure-does-not-look-like-a-judgement")
    assert github_anchor("6. The R4B/R4 gap — issue #19") == "6-the-r4br4-gap--issue-19"
    assert github_anchor("7.1 The undecidable silence — issue #17, **settled**") == (
        "71-the-undecidable-silence--issue-17-settled"
    )


def test_repeated_headings_get_suffixed_anchors() -> None:
    anchors = Anchors()
    assert [
        anchors.of("Configuration"),
        anchors.of("Configuration"),
        anchors.of("Configuration"),
    ] == [
        "configuration",
        "configuration-1",
        "configuration-2",
    ]


_PAGE = """---
title: {title}
type: {kind}
sources:
- path: docs/doctrine.md
  commit: {commit}
status: {status}
---
Body.
"""


def _page(title: str, kind: str = "lesson", status: str = "current") -> str:
    return _PAGE.format(title=title, kind=kind, status=status, commit="a" * 40)


def _index_fixture(root: Path) -> None:
    write(
        root,
        {
            ".claude/project.toml": PROJECT,
            "docs/wiki/lessons/b.md": _page("Beta"),
            "docs/wiki/lessons/a.md": _page("Alpha"),
            "docs/wiki/lessons/old.md": _page("Old", status="superseded"),
            "docs/wiki/rules/r.md": _page("A rule", kind="rule"),
            "CONTEXT.md": "# Context\n\n## Terms\n\n**Proposition**: a write awaiting a human.\n",
            "docs/adr/0001-no-mcp-server.md": "# 1. No MCP server\n",
        },
    )


def test_index_is_deterministic(tmp_path: Path) -> None:
    _index_fixture(tmp_path)
    project = load_project(tmp_path)
    assert render_index(project) == render_index(project)


def test_index_lists_pages_terms_and_adrs(tmp_path: Path) -> None:
    _index_fixture(tmp_path)
    index = render_index(load_project(tmp_path))
    assert index.index("- [Alpha](lessons/a.md)") < index.index("- [Beta](lessons/b.md)")
    assert "- [A rule](rules/r.md)" in index
    assert "Old" not in index
    assert "- [Proposition](../../CONTEXT.md#terms)" in index
    assert "- [1. No MCP server](../adr/0001-no-mcp-server.md)" in index


def test_index_sections_come_from_the_project(tmp_path: Path) -> None:
    _index_fixture(tmp_path)
    sections = (
        '\n[[wiki.index_sections]]\ntitle = "Research"\ndir = "docs/research"\nglob = "*.md"\n'
    )
    write(
        tmp_path,
        {
            ".claude/project.toml": PROJECT + sections,
            "docs/research/2026-10-12-survey.md": "# Survey\n",
        },
    )
    index = render_index(load_project(tmp_path))
    assert "## Research\n\n- [2026-10-12-survey.md](../../docs/research/2026-10-12-survey.md)" in (
        index
    )


def _check(root: Path, base: str | None = None, packs: Mapping[str, Pack] | None = None):
    return check(load_project(root), base, packs)


def _rules(root: Path, base: str | None = None) -> set[int]:
    return {fault.rule for fault in _check(root, base)}


def _edit(root: Path, path: str, old: str, new: str) -> None:
    file = root / path
    file.write_text(file.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def test_a_page_outside_its_type_directory_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    (tmp_path / "docs/wiki/lessons/the-first-lesson.md").rename(
        tmp_path / "docs/wiki/rules/the-first-lesson.md"
    )
    faults = _check(tmp_path)
    assert any(f.rule == 2 and f.path == "docs/wiki/rules/the-first-lesson.md" for f in faults)


def test_a_front_matter_missing_a_field_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    for field_line in ("status: current\n", "type: lesson\n"):
        _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", field_line, "")
    faults = [f for f in _check(tmp_path) if f.rule == 2]
    assert any("type" in f.message for f in faults)


def test_a_source_without_path_or_full_commit_is_refused(tmp_path: Path) -> None:
    pin = clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", pin, pin[:12])
    assert 2 in _rules(tmp_path)


def test_a_superseded_page_without_a_live_successor_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(
        tmp_path,
        "docs/wiki/lessons/the-first-lesson.md",
        "status: current",
        "status: superseded\nsuperseded_by: docs/wiki/lessons/gone.md",
    )
    assert any(f.rule == 2 and "superseded_by" in f.message for f in _check(tmp_path))


def test_a_tracked_page_without_issues_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/defects/the-settled-defect.md", "issues: [21]\n", "")
    assert any(f.rule == 2 and "issues" in f.message for f in _check(tmp_path))


def test_a_duplicate_slug_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    text = (tmp_path / "docs/wiki/lessons/the-first-lesson.md").read_text(encoding="utf-8")
    write(
        tmp_path,
        {"docs/wiki/rules/the-first-lesson.md": text.replace("type: lesson", "type: rule")},
    )
    assert any(f.rule == 2 and "slug" in f.message for f in _check(tmp_path))


def test_a_slug_outside_lowercase_letters_digits_and_hyphens_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    page = tmp_path / "docs/wiki/lessons/the-first-lesson.md"
    page.rename(page.with_name("the_first_lesson.md"))
    assert any(f.rule == 2 and "[a-z0-9-]" in f.message for f in _check(tmp_path))


def test_a_slug_over_forty_characters_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    long = "docs/wiki/lessons/" + "x" * 41 + ".md"
    (tmp_path / "docs/wiki/lessons/the-first-lesson.md").rename(tmp_path / long)
    assert any(f.rule == 2 and "40" in f.message for f in _check(tmp_path))


def test_a_stale_index_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/index.md", "The first lesson", "A stale title")
    assert 1 in _rules(tmp_path)
    assert any(
        f.rule == 1 and "uv run python -m scripts.wiki index" in f.message for f in _check(tmp_path)
    )


def test_a_hand_kept_index_is_not_checked(tmp_path: Path) -> None:
    clean_wiki(tmp_path, PROJECT.replace('tooling = "cpt"', 'tooling = "none"'))
    _edit(tmp_path, "docs/wiki/index.md", "The first lesson", "A hand-written title")
    assert 1 not in _rules(tmp_path)
    assert main(["wiki", "index", "--root", str(tmp_path)]) == 1
    index = (tmp_path / "docs/wiki/index.md").read_text(encoding="utf-8")
    assert "A hand-written title" in index


def test_a_broken_internal_link_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(
        tmp_path,
        "docs/wiki/lessons/the-first-lesson.md",
        "Body of 2.1",
        "Body of 2.1, [x](gone.md)",
    )
    assert 3 in _rules(tmp_path)
    clean_wiki(tmp_path)
    nested = "Body of 2.1, [[A lesson on its own](a-lesson-on-its-own.md)](the-first-lesson.md)"
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "Body of 2.1", nested)
    assert any(f.rule == 3 and "inside a link" in f.message for f in _check(tmp_path))


def test_an_orphan_page_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    text = (tmp_path / "docs/wiki/lessons/the-first-lesson.md").read_text(encoding="utf-8")
    write(tmp_path, {"docs/wiki/lessons/lonely.md": text})
    assert any(f.rule == 4 and f.path == "docs/wiki/lessons/lonely.md" for f in _check(tmp_path))


def test_an_unresolved_wiki_citation_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    fixture_commit(tmp_path, {"src/x.py": "# see wiki:lessons/nowhere\n"})
    assert 5 in _rules(tmp_path)


def test_an_archived_file_is_not_scanned(tmp_path: Path) -> None:
    archive = '[wiki]\narchive_until = 2026-10-12\narchive_named = ["tests/old.py"]\n'
    clean_wiki(tmp_path, PROJECT.replace("[wiki]\n", archive))
    fixture_commit(
        tmp_path,
        {
            "tests/old.py": "# wiki:lessons/nowhere\n",
            "docs/superpowers/plans/2026-10-12-old.md": "wiki:lessons/nowhere\n",
            "docs/superpowers/plans/2026-10-13-new.md": "wiki:lessons/nowhere\n",
        },
    )
    faults = [f for f in _check(tmp_path) if f.rule == 5]
    assert [f.path for f in faults] == ["docs/superpowers/plans/2026-10-13-new.md"]


def test_without_archive_keys_every_file_is_scanned(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    fixture_commit(tmp_path, {"docs/superpowers/plans/2026-01-01-old.md": "wiki:lessons/no\n"})
    assert 5 in _rules(tmp_path)


def test_a_foreign_issue_reference_in_a_page_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "candle-legacy#40", "#40")
    assert 7 in _rules(tmp_path)
    assert any("not candle-legacy's" in f.message for f in _check(tmp_path) if f.rule == 7)


def test_an_issue_url_of_the_repository_itself_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    url = "https://github.com/aneuraz/candle/issues/40"
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "candle-legacy#40", url)
    assert 7 in _rules(tmp_path)


def test_other_issue_reference_form(tmp_path: Path) -> None:
    own = PROJECT.replace(
        'issue_repository = "aneuraz/candle-legacy"\nissue_reference = "candle-legacy#{n}"',
        'issue_repository = "aneuraz/candle"\nissue_reference = "#{n}"',
    )
    clean_wiki(tmp_path, own)
    for page in ("lessons/the-first-lesson.md", "lessons/a-lesson-on-its-own.md"):
        _edit(tmp_path, f"docs/wiki/{page}", "candle-legacy#", "#")
    _edit(tmp_path, "docs/wiki/defects/the-settled-defect.md", "candle-legacy#21", "#21")
    write(tmp_path, {"docs/wiki/index.md": render_index(load_project(tmp_path))})
    assert _check(tmp_path) == []
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "see #40", "see candle#40")
    assert 7 in _rules(tmp_path)


def test_without_an_issue_reference_rule_7_is_skipped(tmp_path: Path) -> None:
    clean_wiki(tmp_path, PROJECT.replace('issue_reference = "candle-legacy#{n}"\n', ""))
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "candle-legacy#40", "#40")
    assert 7 not in _rules(tmp_path)


def test_a_rewritten_log_line_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    base = fixture_commit(tmp_path)
    _edit(tmp_path, "docs/wiki/log.md", "migrate", "rewritten")
    fixture_commit(tmp_path)
    assert 10 in _rules(tmp_path, base)


def test_the_log_rule_is_skipped_without_a_base(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/log.md", "migrate", "rewritten")
    assert 10 not in _rules(tmp_path, None)
    assert 10 not in _rules(tmp_path, "no-such-ref")
    assert 10 not in _rules(tmp_path, "HEAD")


def test_a_front_matter_with_an_unknown_status_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "status: current", "status: curent")
    assert any(f.rule == 2 and "status" in f.message for f in _check(tmp_path))


def test_a_front_matter_with_an_empty_title_is_refused(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, "docs/wiki/lessons/the-first-lesson.md", "title: The first lesson", 'title: ""')
    assert any(f.rule == 2 and "title" in f.message for f in _check(tmp_path))


def test_a_clean_wiki_passes(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    clean_wiki(tmp_path)
    assert _check(tmp_path) == []
    assert main(["wiki", "check", "--root", str(tmp_path)]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()) == 1


LESSON = "docs/wiki/lessons/the-first-lesson.md"


def test_a_front_matter_that_is_not_yaml_is_refused_not_a_crash(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, LESSON, "title: The first lesson", "title: Retries: why they are bounded")
    faults = [f for f in _check(tmp_path) if f.rule == 2]
    assert any(f.path == LESSON and "not valid YAML" in f.message for f in faults)
    assert main(["wiki", "index", "--root", str(tmp_path)]) == 0
    assert "Retries" not in (tmp_path / "docs/wiki/index.md").read_text(encoding="utf-8")


def test_a_bare_title_key_is_an_empty_title(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    _edit(tmp_path, LESSON, "title: The first lesson", "title:")
    assert any(f.rule == 2 and "title is empty" in f.message for f in _check(tmp_path))


def test_check_help_names_every_rule(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as stopped:
        main(["wiki", "check", "--help"])
    assert stopped.value.code == 0
    out = capsys.readouterr().out
    assert sorted(RULES) == [1, 2, 3, 4, 5, 7, 10]
    missing = [n for n, rule in RULES.items() if f"rule {n}: {rule}" not in out]
    assert missing == []


def test_no_project_toml(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["wiki", "check", "--root", str(tmp_path)]) == 1
    assert "no [wiki] in .claude/project.toml" in capsys.readouterr().err
    assert main(["wiki", "index", "--root", str(tmp_path)]) == 1
    assert not (tmp_path / "docs").exists()


def test_a_malformed_project_toml_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    write(tmp_path, {".claude/project.toml": "[wiki]\npath = 3\n"})
    assert main(["wiki", "check", "--root", str(tmp_path)]) == 1
    assert "wiki.path" in capsys.readouterr().err


# Pack citations: `<pack>:<slug>`, resolved against the packs the package carries.


def _with_packs(root: Path) -> Mapping[str, Pack]:
    write_pack(
        root,
        "rules-security",
        {
            "parameterised-sql": rule("Parameterised SQL", "Bind every value.\n"),
            "no-string-sql": rule("No string SQL", superseded_by="parameterised-sql"),
        },
    )
    return load_packs(root)


def test_pack_citation_resolves(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    packs = _with_packs(tmp_path)
    fixture_commit(tmp_path, {"src/x.py": "# see rules-security:parameterised-sql\n"})
    assert lint(load_project(tmp_path), None, packs) == ([], [])


def test_superseded_citation_reports_new_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    clean_wiki(tmp_path)
    packs = _with_packs(tmp_path)
    fixture_commit(tmp_path, {"src/x.py": "\n# see rules-security:no-string-sql\n"})
    faults, notices = lint(load_project(tmp_path), None, packs)
    assert faults == []
    assert [str(n) for n in notices] == [
        "src/x.py:2: rules-security:no-string-sql is superseded: cite "
        "rules-security:parameterised-sql"
    ]
    monkeypatch.setattr("claude_plugins_tools.wiki.cli.load_packs", lambda: packs)
    assert main(["wiki", "check", "--root", str(tmp_path)]) == 0
    assert "cite rules-security:parameterised-sql" in capsys.readouterr().out


def test_unknown_pack_citation_is_a_fault(tmp_path: Path) -> None:
    clean_wiki(tmp_path)
    packs = _with_packs(tmp_path)
    fixture_commit(
        tmp_path,
        {
            "src/x.py": "# rules-security:no-such-rule\n",
            "docs/wiki/lessons/a-lesson-on-its-own.md": (
                tmp_path / "docs/wiki/lessons/a-lesson-on-its-own.md"
            ).read_text(encoding="utf-8")
            + "See rules-nowhere:anything.\n",
        },
    )
    assert _check(tmp_path, None, packs) == [
        Fault(
            "docs/wiki/lessons/a-lesson-on-its-own.md",
            10,
            5,
            "rules-nowhere:anything names no pack rule",
        ),
        Fault("src/x.py", 1, 5, "rules-security:no-such-rule names no pack rule"),
    ]
