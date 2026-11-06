"""Tests of tools/migrate_citations.py, imported by path (`tools` is not a package)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "tools" / "migrate_citations.py"
_SPEC = importlib.util.spec_from_file_location("migrate_citations", _PATH)
assert _SPEC
assert _SPEC.loader
mc = importlib.util.module_from_spec(_SPEC)
sys.modules["migrate_citations"] = mc
_SPEC.loader.exec_module(mc)

TABLE_MD = """\
| source | target | split | note |
|---|---|---|---|
| candle:x | rules-security:x | | |
| candle:sp | rules-security:sp | yes | |
| candle:st | stays | | |
| candle:co | core:some-skill | | |
| candle:CLAUDE.md#4-completion-gate | rules-python:ruff | | |
| candle:SECURITY.md | rules-health-data:breach | | |
| capture:§1.1 | rules-rust:toolchain | | |
"""

REPO = Path("/repo")


@pytest.fixture
def table(tmp_path: Path):
    path = tmp_path / "c.md"
    path.write_text(TABLE_MD, encoding="utf-8")
    return mc.load_classification(path, "candle")


def run(text, file, table, kind="markdown"):
    return mc.rewrite(text, REPO / file, REPO, kind, table)


def test_code_citation_rewritten(table):
    new, events = run("# see wiki:rules/x here", "src/a.py", table, "code")
    assert new == "# see rules-security:x here"
    assert [e.kind for e in events] == ["rewrite"]


@pytest.mark.parametrize(
    ("file", "target"),
    [
        ("docs/wiki/decisions/d.md", "../rules/x.md"),
        (".claude/skills/s/SKILL.md", "../../../docs/wiki/rules/x.md"),
        ("examples/README.md", "../docs/wiki/rules/x.md"),
        ("docs/guide.md", "wiki/rules/x.md"),
        ("docs/wiki/rules/y.md", "x.md"),
    ],
)
def test_markdown_link_rewritten(table, file, target):
    new, events = run(f"See [the rule]({target}).", file, table)
    assert new == "See the rule (`rules-security:x`)."
    assert events[0].kind == "rewrite"


def test_split_slug_kept(table):
    text = "[s](../rules/sp.md) wiki:rules/sp"
    new, events = run(text, "docs/wiki/decisions/a.md", table)
    assert new == text
    assert [e.kind for e in events] == ["kept", "kept"]


def test_stays_slug_kept(table):
    text = "[s](../rules/st.md) [c](../rules/co.md)"
    new, events = run(text, "docs/wiki/decisions/a.md", table)
    assert new == text
    assert [e.kind for e in events] == ["kept", "kept"]


def test_non_slug_rows_skipped(table):
    assert set(table) == {"x", "sp", "st", "co"}


def test_anchor_link_unmapped(table):
    text = "[s](../rules/x.md#part)"
    new, events = run(text, "docs/wiki/decisions/a.md", table)
    assert new == text
    assert events[0].kind == "unmapped"


# --- command line, on a real git repository ---


def git(repo: Path, *args: str):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)  # noqa: S603, S607


def make_repo(tmp_path: Path, files: dict[str, str], project: str = "") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q")
    files = {**files}
    if project:
        files[".claude/project.toml"] = project
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    git(repo, "add", "-A")
    return repo


def cli(repo: Path, *extra: str) -> int:
    path = repo.parent / "c.md"
    path.write_text(TABLE_MD, encoding="utf-8")
    return mc.main(
        ["--repo", str(repo), "--source", "candle", "--classification", str(path), *extra]
    )


BASE = {
    "docs/wiki/rules/x.md": "# x\n",
    "docs/wiki/rules/sp.md": "# sp\n",
    "src/a.py": "# wiki:rules/x\n",
    "docs/wiki/log.md": "- [x](rules/x.md)\n",
}
DATED = "docs/superpowers/specs/2026-10-01-old.md"


def test_log_md_skipped(tmp_path):
    repo = make_repo(tmp_path, BASE)
    assert cli(repo, "--apply") == 0
    assert (repo / "docs/wiki/log.md").read_text() == "- [x](rules/x.md)\n"
    assert (repo / "src/a.py").read_text() == "# rules-security:x\n"


def test_archived_file_skipped(tmp_path):
    content = "wiki:rules/nope wiki:rules/x\n"
    repo = make_repo(tmp_path, {**BASE, DATED: content}, "[wiki]\narchive_until = 2026-10-01\n")
    assert cli(repo, "--apply") == 0
    assert (repo / DATED).read_text() == content


def test_dated_file_after_archive_rewritten(tmp_path):
    repo = make_repo(
        tmp_path, {**BASE, DATED: "wiki:rules/x\n"}, "[wiki]\narchive_until = 2026-09-30\n"
    )
    assert cli(repo, "--apply") == 0
    assert (repo / DATED).read_text() == "rules-security:x\n"


def test_apply_deletes_moved_pages_only(tmp_path):
    repo = make_repo(tmp_path, BASE)
    assert cli(repo, "--apply") == 0
    assert not (repo / "docs/wiki/rules/x.md").exists()
    assert (repo / "docs/wiki/rules/sp.md").exists()


def test_unknown_slug_unmapped_exit_1(tmp_path, capsys):
    repo = make_repo(tmp_path, {**BASE, "src/b.py": "# wiki:rules/nope\n"})
    assert cli(repo) == 1
    assert "UNMAPPED" in capsys.readouterr().out


def test_apply_writes_nothing_when_unmapped(tmp_path):
    repo = make_repo(tmp_path, {**BASE, "src/b.py": "# wiki:rules/nope\n"})
    assert cli(repo, "--apply") == 1
    assert (repo / "src/a.py").read_text() == "# wiki:rules/x\n"
    assert (repo / "docs/wiki/rules/x.md").exists()


def test_dry_run_changes_nothing(tmp_path, capsys):
    repo = make_repo(tmp_path, BASE)
    assert cli(repo) == 0
    assert (repo / "src/a.py").read_text() == "# wiki:rules/x\n"
    assert (repo / "docs/wiki/rules/x.md").exists()
    assert "delete    docs/wiki/rules/x.md" in capsys.readouterr().out


def test_code_fences_untouched_and_kept(table):
    text = "```md\n[a](wiki/rules/x.md)\nwiki:rules/x\n```\nafter wiki:rules/x\n"
    new, events = run(text, "docs/guide.md", table)
    assert new == "```md\n[a](wiki/rules/x.md)\nwiki:rules/x\n```\nafter rules-security:x\n"
    assert [(e.kind, e.line) for e in events] == [("kept", 3), ("kept", 2), ("rewrite", 5)] or {
        (e.kind, e.line) for e in events
    } == {("kept", 2), ("kept", 3), ("rewrite", 5)}
    assert all(e.reason == "inside a code fence" for e in events if e.kind == "kept")


def test_tilde_fence_and_unclosed(table):
    text = "~~~\nwiki:rules/x\n~~~\n"
    assert run(text, "docs/guide.md", table)[0] == text


@pytest.mark.parametrize(
    "line",
    [
        "[a [b] c](wiki/rules/x.md)",
        "[a](<wiki/rules/x.md>)",
        "[a](wiki/rules/x.md?plain=1)",
        "[r]: wiki/rules/x.md",
        "![img](wiki/rules/x.md)",
    ],
)
def test_unhandled_link_forms_unmapped(table, line):
    new, events = run(line + "\n", "docs/guide.md", table)
    assert new == line + "\n"
    assert [e.kind for e in events] == ["unmapped"]
    assert events[0].reason == "link form not handled"


def test_handled_link_not_double_reported(table):
    _, events = run("[a](wiki/rules/x.md#frag)\n", "docs/guide.md", table)
    assert [e.reason for e in events] == ["anchor on a moved page"]
