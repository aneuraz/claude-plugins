"""The rule packs the package carries, and how a `<pack>:<slug>` citation resolves.

A pack's rules are `plugins/rules-<pack>/skills/rules-<pack>/rules/<slug>.md`, one rule per
file. The wheel force-includes `plugins/` as `claude_plugins_tools/plugins`; run from a source
checkout (`uv run` installs the package editable, from `src/`), that directory does not exist and
the repository's own `plugins/` is read instead.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Final

from claude_plugins_tools.wiki.model import split_front_matter

RULES_GLOB: Final = "rules-*/skills/rules-*/rules/*.md"
MARKETPLACE: Final = "datazard-plugins"
SETTINGS: Final = Path(".claude/settings.json")
#: The repository's plugins/ when this module runs from src/claude_plugins_tools/.
_CHECKOUT: Final = Path(__file__).resolve().parents[2] / "plugins"


class UnknownCitation(Exception):  # noqa: N818 — the interface's name
    """A `<pack>:<slug>` citation that names no rule of the packs."""


@dataclass(frozen=True)
class Rule:
    slug: str
    title: str
    path: Path
    superseded_by: str | None


@dataclass(frozen=True)
class Pack:
    name: str
    rules: Mapping[str, Rule]


def _bundled() -> Path:
    installed = Path(str(resources.files("claude_plugins_tools"))) / "plugins"
    return installed if installed.is_dir() else _CHECKOUT


def _rule(file: Path) -> Rule:
    raw, _ = split_front_matter(file.read_text(encoding="utf-8"))
    raw = raw or {}
    successor = raw.get("superseded_by")
    return Rule(
        slug=file.stem,
        title=str(raw.get("title") or file.stem),
        path=file,
        superseded_by=str(successor) if successor else None,
    )


def load_packs(root: Path | None = None) -> Mapping[str, Pack]:
    """The packs under `<root>/plugins/`; with no root, the packs the package carries."""
    plugins = _bundled() if root is None else Path(root) / "plugins"
    rules: dict[str, dict[str, Rule]] = {}
    for file in sorted(plugins.glob(RULES_GLOB)):
        rules.setdefault(file.parents[3].name, {})[file.stem] = _rule(file)
    return {name: Pack(name, found) for name, found in rules.items()}


def resolve(citation: str, packs: Mapping[str, Pack]) -> Rule:
    """The rule `citation` names, through its `superseded_by` (followed once)."""
    name, _, slug = citation.partition(":")
    pack = packs.get(name)
    found = pack.rules.get(slug) if pack else None
    if pack is None or found is None:
        raise UnknownCitation(f"{citation} names no pack rule")
    if found.superseded_by is None:
        return found
    successor = pack.rules.get(found.superseded_by)
    if successor is None:
        raise UnknownCitation(
            f"{citation} is superseded by {name}:{found.superseded_by}, which names no pack rule"
        )
    return successor


def enabled_packs(root: Path, packs: Mapping[str, Pack]) -> tuple[Mapping[str, Pack], str | None]:
    """The packs `<root>/.claude/settings.json` enables (`enabledPlugins`
    `rules-<pack>@datazard-plugins: true`), and None; with no such entry, every pack and a note
    saying so."""
    file = Path(root) / SETTINGS
    try:
        settings = json.loads(file.read_text(encoding="utf-8")) if file.is_file() else {}
        plugins = settings.get("enabledPlugins") or {}
        entries = {
            key.removesuffix(f"@{MARKETPLACE}"): value
            for key, value in plugins.items()
            if key.startswith("rules-") and key.endswith(f"@{MARKETPLACE}")
        }
    except OSError, ValueError, AttributeError:
        entries = {}
    if not entries:
        return packs, f"no rules-*@{MARKETPLACE} in {SETTINGS}: searching every bundled pack"
    return {name: pack for name, pack in packs.items() if entries.get(name) is True}, None
