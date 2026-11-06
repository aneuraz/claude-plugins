"""The project-side facts file, `.claude/project.toml`, and its reader."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

FILE = Path(".claude/project.toml")


class ProjectError(Exception):
    """A malformed `.claude/project.toml`; the message names the file and the key."""


@dataclass(frozen=True)
class IndexSection:
    title: str
    dir: str
    glob: str


@dataclass(frozen=True)
class Surface:
    name: str
    command: str
    description: str


@dataclass(frozen=True)
class Project:
    root: Path
    # [repository]
    name: str | None = None
    siblings: tuple[str, ...] = ()
    issue_repository: str | None = None
    issue_reference: str | None = None
    foreign_commit_url: str | None = None
    # [tooling]
    command: str | None = None
    # [wiki]
    wiki_path: str | None = None
    wiki_tooling: str | None = None
    archive_until: date | None = None
    archive_named: tuple[str, ...] = ()
    index_sections: tuple[IndexSection, ...] = ()
    # [tracking]
    project: str | None = None
    rule_page: str | None = None
    # [qa]
    up: str | None = None
    down: str | None = None
    status: str | None = None
    guard: str | None = None
    up_keep: str | None = None
    down_respect_keep: str | None = None
    variables: tuple[str, ...] = ()
    surfaces: tuple[Surface, ...] = ()
    work_dir: str | None = None
    errors_dir: str | None = None
    tooling_paths: tuple[str, ...] = ()


def _str(value: object) -> bool:
    return isinstance(value, str)


def _strs(value: object) -> bool:
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _tables(fields: tuple[str, ...]):
    def check(value: object) -> bool:
        return isinstance(value, list) and all(
            isinstance(item, dict) and set(item) == set(fields) and all(map(_str, item.values()))
            for item in value
        )

    return check


def _is_date(value: object) -> bool:
    return isinstance(value, date)


def _one_of(*allowed: str):
    return lambda value: value in allowed


_SCHEMA: dict[str, dict[str, Any]] = {
    "repository": {
        "name": _str,
        "siblings": _strs,
        "issue_repository": _str,
        "issue_reference": _str,
        "foreign_commit_url": _str,
    },
    "tooling": {"command": _str},
    "wiki": {
        "path": _str,
        "tooling": _one_of("cpt", "none"),
        "archive_until": _is_date,
        "archive_named": _strs,
        "index_sections": _tables(("title", "dir", "glob")),
    },
    "tracking": {"project": _str, "rule_page": _str},
    "qa": {
        "up": _str,
        "down": _str,
        "status": _str,
        "guard": _str,
        "up_keep": _str,
        "down_respect_keep": _str,
        "variables": _strs,
        "surfaces": _tables(("name", "command", "description")),
        "work_dir": _str,
        "errors_dir": _str,
        "tooling_paths": _strs,
    },
}

# (section, key) -> Project field
_FIELDS = {
    ("wiki", "path"): "wiki_path",
    ("wiki", "tooling"): "wiki_tooling",
}


def _build(key: str, value: Any) -> Any:
    if key == "index_sections":
        return tuple(IndexSection(**item) for item in value)
    if key == "surfaces":
        return tuple(Surface(**item) for item in value)
    if isinstance(value, list):
        return tuple(value)
    return value


def load_project(root: Path) -> Project:
    """Read `<root>/.claude/project.toml`; a missing file yields an unconfigured Project."""
    root = Path(root)
    path = root / FILE
    if not path.is_file():
        return Project(root=root)
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise ProjectError(f"{path}: not valid TOML: {error}") from error

    values: dict[str, Any] = {}
    for section, table in data.items():
        if section not in _SCHEMA:
            raise ProjectError(f"{path}: unknown section {section!r}")
        if not isinstance(table, dict):
            raise ProjectError(f"{path}: {section} must be a table")
        for key, value in table.items():
            check = _SCHEMA[section].get(key)
            if check is None:
                raise ProjectError(f"{path}: unknown key {section}.{key}")
            if not check(value):
                raise ProjectError(f"{path}: {section}.{key} has an invalid value: {value!r}")
            field = _FIELDS.get((section, key), key)
            values[field] = _build(key, value)
    return Project(root=root, **values)
