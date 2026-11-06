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
from collections.abc import Mapping
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
_LINK = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)((?:\s+\"[^\"]*\")?)\)")
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


_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_PATH = re.compile(r"[\w./-]+\.md")
_LINKY = re.compile(r"(?:[(<]|\]:\s*)$")


def _chunks(text: str) -> list[tuple[bool, int, str]]:
    """Split Markdown into (fenced, first line number, text) runs."""
    runs: list[tuple[bool, int, str]] = []
    fence: str | None = None
    for number, line in enumerate(text.splitlines(keepends=True), start=1):
        marker = _FENCE.match(line)
        if fence is None and marker:
            fence, fenced = marker.group(1), True
        elif (
            fence is not None
            and marker
            and marker.group(1)[0] == fence[0]
            and len(marker.group(1)) >= len(fence)
            and not line.strip().strip(fence[0])
        ):
            fence, fenced = None, True
        else:
            fenced = fence is not None
        if runs and runs[-1][0] == fenced:
            runs[-1] = (fenced, runs[-1][1], runs[-1][2] + line)
        else:
            runs.append((fenced, number, line))
    return runs


def rewrite(
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

    def chunk(part: str, first: int, fenced: bool) -> str:
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
                        "inside a code fence",
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

        # `result` and `part` differ only inside code citations, never in newlines.
        def link(match: re.Match[str]) -> str:
            label, destination = match.group(1), match.group(2)
            path, _, fragment = destination.partition("#")
            if not path.endswith(".md") or _SCHEME.match(path):
                return match.group(0)
            slug = rules_slug(path)
            if slug is None:
                return match.group(0)
            handled.append(match.span())
            line = first + result.count("\n", 0, match.start())
            if fenced:
                events.append(Event("kept", rel, line, match.group(0), None, "inside a code fence"))
                return match.group(0)
            target = table.get(slug)
            new = f"{label} (`{target.pack_citation}`)" if target and target.pack_citation else ""
            return decide(slug, fragment, match.group(0), new, line)

        out = _LINK.sub(link, result)
        if not fenced:
            # Residual scan: a reference to a moved or unknown rule page that no pass handled.
            for found in _PATH.finditer(result):
                slug = rules_slug(found.group(0))
                if (
                    slug is None
                    or not ("rules/" in found.group(0) or _LINKY.search(result[: found.start()]))
                    or any(s <= found.start() < e for s, e in handled)
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
        return chunk(text, 1, fenced=False), events
    return "".join(chunk(part, first, fenced) for fenced, first, part in _chunks(text)), events


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
        events.extend(found)
        if new_text != text:
            changes[path] = new_text

    for event in events:
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
