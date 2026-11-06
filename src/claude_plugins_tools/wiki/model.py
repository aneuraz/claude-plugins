"""Pages, their types and their front matter (design §3)."""

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

import yaml

from claude_plugins_tools.project import Project
from claude_plugins_tools.wiki.errors import WikiError

SLUG_MAX: Final = 40
SLUG: Final = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
COMMIT: Final = re.compile(r"[0-9a-f]{40}")


class PageType(StrEnum):
    HUB = "hub"
    LESSON = "lesson"
    RULE = "rule"
    DEFECT = "defect"
    DEBT = "debt"
    DECISION = "decision"
    REFERENCE = "reference"
    HOWTO = "howto"


DIRECTORY: Final[dict[PageType, str]] = {
    PageType.HUB: "hubs",
    PageType.LESSON: "lessons",
    PageType.RULE: "rules",
    PageType.DEFECT: "defects",
    PageType.DEBT: "debts",
    PageType.DECISION: "decisions",
    PageType.REFERENCE: "reference",
    PageType.HOWTO: "howto",
}
#: Types whose pages carry the issues they record.
TRACKED: Final = frozenset({PageType.DEBT, PageType.DEFECT, PageType.DECISION})


def wiki_dir(project: Project) -> Path:
    """The wiki's directory from the repository root: `[wiki] path`."""
    if project.wiki_path is None:
        raise WikiError("no [wiki] in .claude/project.toml: this project has no wiki configured")
    return Path(project.wiki_path)


def log_path(project: Project) -> Path:
    return wiki_dir(project) / "log.md"


class Status(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"


@dataclass(frozen=True)
class Source:
    path: str
    commit: str
    anchor: str | None = None


@dataclass(frozen=True)
class FrontMatter:
    title: str
    kind: PageType
    sources: tuple[Source, ...]
    status: Status = Status.CURRENT
    superseded_by: str | None = None
    summary: str | None = None
    issues: tuple[int, ...] = field(default=())


def render_front_matter(front: FrontMatter) -> str:
    sources = []
    for source in front.sources:
        entry: dict[str, str] = {"path": source.path, "commit": source.commit}
        if source.anchor:
            entry["anchor"] = source.anchor
        sources.append(entry)
    data: dict[str, object] = {
        "title": front.title,
        "type": str(front.kind),
        "sources": sources,
        "status": str(front.status),
    }
    if front.superseded_by:
        data["superseded_by"] = front.superseded_by
    if front.summary:
        data["summary"] = front.summary
    if front.issues:
        data["issues"] = list(front.issues)
    dumped = yaml.safe_dump(
        data, sort_keys=False, allow_unicode=True, width=10_000, default_flow_style=None
    )
    return f"---\n{dumped}---\n"


class FrontMatterError(WikiError):
    """The front matter is not YAML."""


def split_front_matter(text: str) -> tuple[dict[str, object] | None, str]:
    """The front matter as a mapping (None when absent or not a mapping), and the body."""
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return None, text
    try:
        raw = yaml.safe_load(text[4:end])
    except yaml.YAMLError as error:
        problem = " ".join(str(error).split())
        raise FrontMatterError(f"the front matter is not valid YAML: {problem}") from error
    return (raw if isinstance(raw, dict) else None), text[end + 5 :]


def _scalar_faults(raw: dict[str, object]) -> list[str]:
    title = raw["title"]
    faults = [] if title is not None and str(title).strip() else ["the title is empty"]
    if str(raw["status"]) not in set(Status):
        faults.append(f"unknown status {raw['status']}")
    return faults


def front_matter_faults(raw: dict[str, object] | None, path: str, root: Path) -> list[str]:
    if raw is None:
        return ["no front matter"]
    missing = [name for name in ("title", "type", "sources", "status") if name not in raw]
    if missing:
        return [f"the front matter lacks {name}" for name in missing]
    faults: list[str] = []
    faults.extend(_scalar_faults(raw))
    try:
        kind = PageType(str(raw["type"]))
    except ValueError:
        return [f"unknown type {raw['type']}"]
    directory = Path(path).parent.name
    if directory != DIRECTORY[kind]:
        faults.append(f"a {kind} page sits in {directory}/, not {DIRECTORY[kind]}/")
    sources = raw["sources"]
    if not isinstance(sources, list) or not sources:
        faults.append("sources is empty")
    else:
        for source in sources:
            if (
                not isinstance(source, dict)
                or not source.get("path")
                or not COMMIT.fullmatch(str(source.get("commit", "")))
            ):
                faults.append(f"a source lacks a path or a 40-hex commit: {source}")
    if raw["status"] == Status.SUPERSEDED:
        successor = raw.get("superseded_by")
        if not successor or not (root / str(successor)).is_file():
            faults.append(f"superseded_by names no existing page: {successor}")
    if kind in TRACKED and not raw.get("issues"):
        faults.append(f"a {kind} page carries no issues")
    return faults
