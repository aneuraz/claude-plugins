"""Fixture repositories for the wiki tool's tests: files, a git commit, its SHA, and packs."""

import shutil
import subprocess
from pathlib import Path

from claude_plugins_tools.project import load_project
from claude_plugins_tools.wiki import index
from claude_plugins_tools.wiki.model import FrontMatter, PageType, Source, render_front_matter

_GIT = shutil.which("git") or "git"

#: The fixture project: issue references go to aneuraz/candle-legacy, as in candle.
PROJECT = """[repository]
name = "aneuraz/candle"
issue_repository = "aneuraz/candle-legacy"
issue_reference = "candle-legacy#{n}"

[wiki]
path = "docs/wiki"
tooling = "cpt"

[[wiki.index_sections]]
title = "Architecture decisions"
dir = "docs/adr"
glob = "*.md"
"""


def git(root: Path, *args: str) -> str:
    result = subprocess.run(  # noqa: S603 — a fixed argument list in a test helper
        [_GIT, "-c", "user.name=fixture", "-c", "user.email=fixture@example.org", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def write(root: Path, files: dict[str, str]) -> None:
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")


def commit(root: Path, files: dict[str, str] | None = None) -> str:
    """Write the files, commit everything, return the commit's SHA."""
    if not (root / ".git").exists():
        git(root, "init", "-q", "-b", "main")
    if files:
        write(root, files)
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", "fixture")
    return git(root, "rev-parse", "HEAD")


def write_pack(root: Path, pack: str, rules: dict[str, str]) -> None:
    """A pack under `<root>/plugins/<pack>/skills/<pack>/rules/`, one file per slug."""
    write(root, {f"plugins/{pack}/skills/{pack}/rules/{slug}.md": t for slug, t in rules.items()})


def rule(title: str, body: str = "", superseded_by: str | None = None) -> str:
    successor = f"superseded_by: {superseded_by}\n" if superseded_by else ""
    return f"---\ntitle: {title}\n{successor}---\n{body}"


SOURCE = "# Notes\n\nWhere the fixture wiki's pages come from.\n"
CONTEXT = "# Context\n\n## Terms\n\n**Proposition**: a write awaiting a human.\n"
ADR = "# 1. No MCP server\n\nBecause.\n"


def _page(title: str, kind: PageType, pin: str, body: str, issues: tuple[int, ...] = ()) -> str:
    front = FrontMatter(title, kind, (Source("docs/notes.md", pin),), issues=issues)
    return render_front_matter(front) + "\n" + body


def clean_wiki(root: Path, project: str = PROJECT) -> str:
    """A source, the pages that cite it, the log and the index, committed; the source's commit."""
    pin = commit(
        root,
        {
            ".claude/project.toml": project,
            "docs/notes.md": SOURCE,
            "CONTEXT.md": CONTEXT,
            "docs/adr/0001-no-mcp-server.md": ADR,
        },
    )
    lesson, defect = PageType.LESSON, PageType.DEFECT
    write(
        root,
        {
            "docs/wiki/hubs/notes.md": _page(
                "Notes",
                PageType.HUB,
                pin,
                "- [A lesson on its own](../lessons/a-lesson-on-its-own.md)\n"
                "- [The first lesson](../lessons/the-first-lesson.md)\n"
                "- [The settled defect](../defects/the-settled-defect.md)\n"
                "- [Pin every version](../rules/pin-every-version.md)\n",
            ),
            "docs/wiki/rules/pin-every-version.md": _page(
                "Pin every version", PageType.RULE, pin, "Always.\n"
            ),
            "docs/wiki/lessons/a-lesson-on-its-own.md": _page(
                "A lesson on its own", lesson, pin, "Text one, issue candle-legacy#17.\n"
            ),
            "docs/wiki/lessons/the-first-lesson.md": _page(
                "The first lesson",
                lesson,
                pin,
                "Body of 2.1, see candle-legacy#40 and candle-legacy#41.\n",
            ),
            "docs/wiki/defects/the-settled-defect.md": _page(
                "The settled defect — issue candle-legacy#21",
                defect,
                pin,
                "Body of 2.2.\n",
                issues=(21,),
            ),
            "docs/wiki/log.md": "# Log\n\n## [2026-09-19] migrate | Notes\n\n"
            "- [Notes](hubs/notes.md)\n",
        },
    )
    write(root, {"docs/wiki/index.md": index.render_index(load_project(root))})
    commit(root)
    return pin
