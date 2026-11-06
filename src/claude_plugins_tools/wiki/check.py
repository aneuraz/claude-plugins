"""The lint: rules 1 to 5, 7 and 10, one fault per breach.

Rules 6, 8 and 9 checked candle's doctrine migration, which is complete; they are retired
and keep their numbers unused, so a fault message means what it meant in candle. Rule 5 also
resolves `<pack>:<slug>` citations against the packs; one that names a superseded rule is not a
fault: it yields a notice naming the citation to use instead."""

import re
from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

from claude_plugins_tools.packs import Pack, UnknownCitation, load_packs, resolve
from claude_plugins_tools.project import Project
from claude_plugins_tools.wiki.archive import git, scanned_files
from claude_plugins_tools.wiki.errors import WikiError
from claude_plugins_tools.wiki.grammar import PACK_CITATION, WIKI_CITATION, issue_rewriter
from claude_plugins_tools.wiki.index import index_path, render_index
from claude_plugins_tools.wiki.markdown import line_of
from claude_plugins_tools.wiki.model import (
    SLUG,
    SLUG_MAX,
    PageType,
    Status,
    front_matter_faults,
    log_path,
    wiki_dir,
)
from claude_plugins_tools.wiki.pages import Page, internal_links, load_pages

_NESTED: Final = re.compile(r"\[[^\[\]\n]*\[[^\]\n]*\]\([^)\s]*\)[^\]\n]*\]\(")

#: What each rule refuses, by its number; `check --help` prints them.
RULES: Final = {
    1: "index.md differs from what `index` writes (not checked when [wiki] tooling is none)",
    2: "a front matter breaks the page schema, or a page sits outside its type's directory",
    3: (
        "an internal link of the wiki does not resolve to a file "
        "(links on log.md lines identical to a line of the --base log are not checked)"
    ),
    4: "a page other than a hub has no inbound link from another page",
    5: "a wiki: citation names no page, or a <pack>:<slug> citation no pack rule",
    7: "a page holds an issue reference not in [repository] issue_reference's form",
    10: "a line of log.md present on the base branch is changed or removed",
}


@dataclass(frozen=True)
class Fault:
    path: str
    line: int
    rule: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: rule {self.rule}: {self.message}"


@dataclass(frozen=True)
class Notice:
    """Not a fault: a citation that resolves, but through `superseded_by`."""

    path: str
    line: int
    message: str

    def __str__(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def _index(project: Project) -> list[Fault]:
    if project.wiki_tooling == "none":
        return []
    index = index_path(project)
    file = project.root / index
    current = file.read_text(encoding="utf-8") if file.is_file() else ""
    return (
        []
        if current == render_index(project)
        else [
            Fault(
                index.as_posix(),
                1,
                1,
                "differs from what `index` writes: run `wiki index` with the project's cpt"
                " command (`[tooling] command`)",
            )
        ]
    )


def _front_matter(root: Path, pages: list[Page]) -> list[Fault]:
    faults = [
        Fault(p.path, 1, 2, message)
        for p in pages
        for message in ([p.error] if p.error else front_matter_faults(p.raw, p.path, root))
    ]
    slugs = Counter(PurePosixPath(p.path).stem for p in pages)
    for page in pages:
        slug = PurePosixPath(page.path).stem
        if len(slug) > SLUG_MAX:
            faults.append(Fault(page.path, 1, 2, f"the slug is longer than {SLUG_MAX} characters"))
        if not SLUG.fullmatch(slug):
            faults.append(Fault(page.path, 1, 2, f"the slug {slug} is not lowercase [a-z0-9-]"))
        if slugs[slug] > 1:
            faults.append(Fault(page.path, 1, 2, f"the slug {slug} is used by another page"))
    return faults


def _base_log(project: Project, base: str) -> list[str] | None:
    """The lines of the log on `base`, or None when the base or its log cannot be read."""
    try:
        return git(project.root, "show", f"{base}:{log_path(project).as_posix()}").splitlines()
    except WikiError:
        return None


def _links(project: Project, base: str | None) -> list[Fault]:
    root, wiki = project.root, wiki_dir(project)
    log = log_path(project).as_posix()
    history = set(_base_log(project, base) or []) if base is not None else set()
    faults: list[Fault] = []
    for file in sorted((root / wiki).rglob("*.md")):
        path = file.relative_to(root).as_posix()
        text = file.read_text(encoding="utf-8")
        lines = text.splitlines()
        for line, target in internal_links(path, text):
            if path == log and lines[line - 1] in history:
                continue
            if not (root / target).exists():
                faults.append(Fault(path, line, 3, f"links to {target}, which does not exist"))
        for match in _NESTED.finditer(text):
            faults.append(
                Fault(path, line_of(text, match.start()), 3, "a link inside a link's text")
            )
    return faults


def _orphans(pages: list[Page]) -> list[Fault]:
    inbound: Counter[str] = Counter()
    for page in pages:
        for _, target in internal_links(page.path, page.text):
            if target != page.path:
                inbound[target] += 1
    return [
        Fault(p.path, 1, 4, "no other page links to it")
        for p in pages
        if (p.raw or {}).get("type") != PageType.HUB
        and (p.raw or {}).get("status") != Status.SUPERSEDED
        and inbound[p.path] == 0
    ]


def _citations(
    project: Project, pages: list[Page], packs: Mapping[str, Pack]
) -> tuple[list[Fault], list[Notice]]:
    root, wiki = project.root, wiki_dir(project)
    faults: list[Fault] = []
    notices: list[Notice] = []
    texts = [(p.path, p.text) for p in pages] + scanned_files(project)
    for path, text in texts:
        for match in WIKI_CITATION.finditer(text):
            target = wiki / match["directory"] / f"{match['slug']}.md"
            if not (root / target).is_file():
                line = line_of(text, match.start())
                faults.append(Fault(path, line, 5, f"{match[0]} names no page"))
        for match in PACK_CITATION.finditer(text):
            line = line_of(text, match.start())
            try:
                found = resolve(match[0], packs)
            except UnknownCitation as error:
                faults.append(Fault(path, line, 5, str(error)))
                continue
            if found.slug != match["slug"]:
                new = f"{match['pack']}:{found.slug}"
                notices.append(Notice(path, line, f"{match[0]} is superseded: cite {new}"))
    return faults, notices


def _issues(project: Project, pages: list[Page]) -> list[Fault]:
    rewrite = issue_rewriter(project)
    if rewrite is None:
        return []
    owner = (project.issue_repository or "").rpartition("/")[2] or project.issue_reference
    faults: list[Fault] = []
    for page in pages:
        fixed = rewrite(page.text)
        if fixed != page.text:
            lines = zip(page.text.splitlines(), fixed.splitlines(), strict=False)
            line = next((n for n, (a, b) in enumerate(lines, start=1) if a != b), 1)
            faults.append(Fault(page.path, line, 7, f"an issue reference that is not {owner}'s"))
    return faults


def _log(project: Project, base: str) -> list[Fault]:
    root, log = project.root, log_path(project)
    try:
        if (
            git(root, "rev-parse", f"{base}^{{commit}}").strip()
            == git(root, "rev-parse", "HEAD").strip()
        ):
            return []
        before = git(root, "show", f"{base}:{log.as_posix()}").splitlines()
    except WikiError:
        return []
    file = root / log
    after = file.read_text(encoding="utf-8").splitlines() if file.is_file() else []
    for number, line in enumerate(before, start=1):
        if number > len(after) or after[number - 1] != line:
            return [
                Fault(
                    log.as_posix(),
                    number,
                    10,
                    "a line of the base branch's log was changed or removed",
                )
            ]
    return []


def lint(
    project: Project, base: str | None, packs: Mapping[str, Pack] | None = None
) -> tuple[list[Fault], list[Notice]]:
    """The faults and the notices; `packs` defaults to the packs the package carries."""
    root, wiki = project.root, wiki_dir(project)
    pages = load_pages(root, wiki)
    faults = _index(project) + _front_matter(root, pages) + _links(project, base) + _orphans(pages)
    cited, notices = _citations(project, pages, load_packs() if packs is None else packs)
    faults += cited + _issues(project, pages)
    if base is not None:
        faults += _log(project, base)
    return (
        sorted(set(faults), key=lambda f: (f.path, f.line, f.rule, f.message)),
        sorted(set(notices), key=lambda n: (n.path, n.line, n.message)),
    )


def check(
    project: Project, base: str | None, packs: Mapping[str, Pack] | None = None
) -> list[Fault]:
    return lint(project, base, packs)[0]
