"""Rewrite a project's citations of moved rule pages into the rule packs' `<pack>:<slug>` form.

    uv run python tools/migrate_citations.py --repo <path> --source <name> [--apply]

The classification is this repository's `docs/rule-classification.md`; only rows `<name>:<slug>`
count. A page whose target is a `rules-*` pack and is not `split` is moved: its citations are
rewritten and its page deleted. A `split` page, a `stays` page and a `core:` target keep their page
and their citations (reported as kept). Exit 1 when any citation cannot be mapped (a slug with no
row, an anchor on a moved page); then, with `--apply`, nothing is written.
"""

from __future__ import annotations

import argparse
import posixpath
import re
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from claude_plugins_tools.project import load_project
from claude_plugins_tools.wiki.archive import scanned_files

CLASSIFICATION = Path(__file__).resolve().parent.parent / "docs" / "rule-classification.md"
LOG = "docs/wiki/log.md"
RULES_DIR = "docs/wiki/rules"

_SPLIT_CELL = 2
_SLUG = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_CODE = re.compile(r"wiki:rules/([A-Za-z0-9_-]+)(#[\w-]+)?")
_LINK = re.compile(r"(?<!!)\[([^\[\]]*)\]\(([^)\s]+)(\s+(?:\"[^\"]*\"|'[^']*'))?\)")
_SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:")


@dataclass(frozen=True)
class Target:
    #: "<pack>:<slug>" when the target is a `rules-*` pack, else None (`stays`, `core:`).
    pack_citation: str | None
    split: bool

    @property
    def moved(self) -> bool:
        return self.pack_citation is not None and not self.split


@dataclass(frozen=True)
class Event:
    kind: Literal["rewrite", "kept", "unmapped"]
    file: Path
    line: int
    old: str
    new: str | None
    reason: str = ""


def load_classification(path: Path, source: str) -> dict[str, Target]:
    table: dict[str, Target] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) <= _SPLIT_CELL or not cells[0].startswith(f"{source}:"):
            continue
        slug = cells[0].removeprefix(f"{source}:")
        if not _SLUG.match(slug):
            continue
        target = cells[1]
        pack = target if target.startswith("rules-") else None
        table[slug] = Target(pack, cells[2] == "yes")
    return table


_TICKS = re.compile(r"`+")


def _code_spans(text: str) -> list[tuple[int, int]]:
    """Inline code spans (CommonMark: a backtick run closes at the next run of equal length)."""
    runs = [(m.start(), m.end()) for m in _TICKS.finditer(text)]
    spans: list[tuple[int, int]] = []
    i = 0
    while i < len(runs):
        length = runs[i][1] - runs[i][0]
        close = next(
            (j for j in range(i + 1, len(runs)) if runs[j][1] - runs[j][0] == length), None
        )
        if close is None:
            i += 1
            continue
        spans.append((runs[i][0], runs[close][1]))
        i = close + 1
    return spans


def _sub_links(
    text: str,
    spans: list[tuple[int, int]],
    link: Callable[[re.Match[str], bool], str],
) -> str:
    """`_LINK.sub` where a `[` inside an inline code span cannot open a label leaving the span."""
    pieces: list[str] = []
    pos = 0
    while match := _LINK.search(text, pos):
        start = match.start()
        host = next((s for s in spans if s[0] <= start < s[1]), None)
        if host is not None and match.end() > host[1]:
            pieces.append(text[pos : start + 1])
            pos = start + 1
            continue
        pieces.append(text[pos:start])
        pieces.append(link(match, host is not None))
        pos = match.end()
    pieces.append(text[pos:])
    return "".join(pieces)


_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_PATH = re.compile(r"[\w./-]+\.md")
_LINKY = re.compile(r"(?:[(<\"']|\(\s+|\]:\s*)$")


_LIST_ITEM = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s")
FENCE_REASON = "inside a code fence"
INDENT_REASON = "inside an indented code block"


def _indented(line: str) -> bool:
    return line.expandtabs(4).startswith("    ") and bool(line.strip())


def _closes(fence: str, marker: str, line: str) -> bool:
    return marker[0] == fence[0] and len(marker) >= len(fence) and not line.strip().strip(fence[0])


def _chunks(text: str) -> list[tuple[str | None, int, str]]:
    """Split Markdown into (code reason or None, first line number, text) runs.

    Code is a fenced block (fence lines indented 0-3 spaces) or a CommonMark indented block (4+
    spaces or a tab, after a blank line, not continuing a paragraph). Under a list item the indented
    lines are item content, not code (conservative: they stay rewritable).
    """
    lines = text.splitlines(keepends=True)
    runs: list[tuple[str | None, int, str]] = []
    fence: str | None = None
    in_list = False
    in_indented = False
    for index, line in enumerate(lines):
        number = index + 1
        marker = _FENCE.match(line)
        reason: str | None
        if fence is None and in_indented and (_indented(line) or not line.strip()):
            # Blank lines stay in the block only when more indented code follows.
            following = next((x for x in lines[index:] if x.strip()), "")
            if line.strip() or _indented(following):
                reason = INDENT_REASON
            else:
                reason, in_indented = None, False
        elif fence is None and marker:
            in_indented = False
            fence, reason = marker.group(1), FENCE_REASON
        elif fence is not None:
            reason = FENCE_REASON
            if marker and _closes(fence, marker.group(1), line):
                fence = None
        else:
            in_indented = False
            previous = lines[index - 1] if index else ""
            after_blank = index == 0 or not previous.strip()
            in_indented = _indented(line) and not in_list and after_blank
            reason = INDENT_REASON if in_indented else None
            if _LIST_ITEM.match(line):
                in_list = True
            elif line.strip() and not line.startswith((" ", "\t")) and after_blank:
                in_list = False
        if runs and runs[-1][0] == reason:
            runs[-1] = (reason, runs[-1][1], runs[-1][2] + line)
        else:
            runs.append((reason, number, line))
    return runs


def rewrite(  # noqa: PLR0915
    text: str,
    file: Path,
    repo: Path,
    kind: Literal["code", "markdown"],
    table: Mapping[str, Target],
) -> tuple[str, list[Event]]:
    rel = file.relative_to(repo) if file.is_absolute() else file
    events: list[Event] = []

    def rules_slug(path: str) -> str | None:
        resolved = posixpath.normpath(posixpath.join(rel.parent.as_posix(), path))
        if posixpath.dirname(resolved) != RULES_DIR:
            return None
        return posixpath.basename(resolved).removesuffix(".md")

    def decide(slug: str, anchor: str, old: str, new: str, line: int) -> str:
        target = table.get(slug)
        if target is None:
            events.append(Event("unmapped", rel, line, old, None, "no classification row"))
            return old
        if not target.moved:
            events.append(Event("kept", rel, line, old, None))
            return old
        if anchor:
            events.append(Event("unmapped", rel, line, old, None, "anchor on a moved page"))
            return old
        events.append(Event("rewrite", rel, line, old, new))
        return new

    def chunk(part: str, first: int, block: str | None) -> str:
        fenced = block is not None

        def line_of(offset: int) -> int:
            return first + part.count("\n", 0, offset)

        def code(match: re.Match[str]) -> str:
            if fenced:
                events.append(
                    Event(
                        "kept",
                        rel,
                        line_of(match.start()),
                        match.group(0),
                        None,
                        block or "",
                    )
                )
                return match.group(0)
            slug, anchor = match.group(1), match.group(2) or ""
            target = table.get(slug)
            new = (target.pack_citation if target else None) or ""
            return decide(slug, anchor, match.group(0), new, line_of(match.start()))

        result = _CODE.sub(code, part)
        if kind == "code":
            return result
        handled: list[tuple[int, int]] = []  # spans of `part` the link pass dealt with
        spans = [] if fenced else _code_spans(result)

        # `result` and `part` differ only inside code citations, never in newlines.
        def link(match: re.Match[str], in_span: bool) -> str:
            label, destination = match.group(1), match.group(2)
            path, _, fragment = destination.partition("#")
            if not path.endswith(".md") or _SCHEME.match(path):
                return match.group(0)
            slug = rules_slug(path)
            if slug is None:
                return match.group(0)
            handled.append(match.span())
            line = first + result.count("\n", 0, match.start())
            if fenced or in_span:
                reason = block or "inside an inline code span"
                events.append(Event("kept", rel, line, match.group(0), None, reason))
                return match.group(0)
            target = table.get(slug)
            if target and target.pack_citation:
                title = (match.group(3) or "").strip()
                new = f"{label} (`{target.pack_citation}`{', ' + title if title else ''})"
            else:
                new = ""
            return decide(slug, fragment, match.group(0), new, line)

        out = _sub_links(result, spans, link)
        if not fenced:
            # Residual scan: a reference to a moved or unknown rule page that no pass handled.
            for found in _PATH.finditer(result):
                slug = rules_slug(found.group(0))
                if (
                    slug is None
                    or not ("rules/" in found.group(0) or _LINKY.search(result[: found.start()]))
                    or any(s <= found.start() < e for s, e in handled)
                    or any(s <= found.start() < e for s, e in spans)
                ):
                    continue
                target = table.get(slug)
                if target is not None and not target.moved:
                    continue
                events.append(
                    Event(
                        "unmapped",
                        rel,
                        first + result.count("\n", 0, found.start()),
                        found.group(0),
                        None,
                        "link form not handled",
                    )
                )
        return out

    if kind == "code":
        return chunk(text, 1, None), events
    out = "".join(chunk(part, first, block) for block, first, part in _chunks(text))
    return out, sorted(events, key=lambda e: e.line)


def _format(event: Event) -> str:
    where = f"{event.file}:{event.line}"
    if event.kind == "rewrite":
        return f"rewrite   {where}: {event.old} -> {event.new}"
    if event.kind == "kept":
        return f"kept      {where}: {event.old}"
    return f"UNMAPPED  {where}: {event.old} ({event.reason})"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--classification", type=Path, default=CLASSIFICATION)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()

    table = load_classification(args.classification, args.source)
    project = load_project(repo)
    doomed = sorted(
        f"{RULES_DIR}/{slug}.md"
        for slug, target in table.items()
        if target.moved and (repo / RULES_DIR / f"{slug}.md").is_file()
    )

    changes: dict[str, str] = {}
    events: list[Event] = []
    for path, text in scanned_files(project):
        if path == LOG or path in doomed:
            continue
        kind: Literal["code", "markdown"] = "markdown" if path.endswith(".md") else "code"
        new_text, found = rewrite(text, Path(path), repo, kind, table)
        events.extend(found)  # `rewrite` orders each file's events by line
        if new_text != text:
            changes[path] = new_text

    for event in sorted(events, key=lambda e: (e.file.as_posix(), e.line)):
        print(_format(event))
    for page in doomed:
        print(f"delete    {page}")
    counts = {k: sum(e.kind == k for e in events) for k in ("rewrite", "kept", "unmapped")}
    print(
        f"{counts['rewrite']} rewritten, {counts['kept']} kept, {counts['unmapped']} unmapped, "
        f"{len(doomed)} page(s) to delete, {len(changes)} file(s) changed"
    )
    if counts["unmapped"]:
        if args.apply:
            print("unmapped citations remain: nothing written")
        return 1
    if args.apply:
        for path, new_text in changes.items():
            (repo / path).write_text(new_text, encoding="utf-8")
        for page in doomed:
            (repo / page).unlink()
    else:
        print("dry run: nothing written (use --apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
