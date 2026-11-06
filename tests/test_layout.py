"""Layout of the marketplace: what sits where, and what a plugin may reference."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
PLUGINS = ROOT / "plugins"

plugin_dirs = sorted(p for p in PLUGINS.iterdir() if p.is_dir()) if PLUGINS.is_dir() else []
skill_files = sorted(PLUGINS.glob("*/skills/*/SKILL.md"))
markdown_files = sorted(PLUGINS.rglob("*.md"))

LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def _ids(paths: list[Path]) -> list[str]:
    return [str(p.relative_to(ROOT)) for p in paths]


def test_marketplace_lists_every_plugin() -> None:
    marketplace = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = marketplace["plugins"]
    assert sorted(e["name"] for e in entries) == sorted(p.name for p in plugin_dirs)
    for entry in entries:
        assert entry["source"] == f"./plugins/{entry['name']}"
        assert "version" not in entry
    for plugin in plugin_dirs:
        manifest = json.loads((plugin / ".claude-plugin" / "plugin.json").read_text())
        assert "version" not in manifest


@pytest.mark.parametrize("plugin", plugin_dirs, ids=lambda p: p.name)
def test_plugin_manifest(plugin: Path) -> None:
    manifest_dir = plugin / ".claude-plugin"
    manifest = json.loads((manifest_dir / "plugin.json").read_text())
    assert manifest["name"] == plugin.name
    assert [p.name for p in manifest_dir.iterdir()] == ["plugin.json"]


@pytest.mark.parametrize("skill", skill_files, ids=_ids(skill_files))
def test_skill_frontmatter(skill: Path) -> None:
    match = FRONTMATTER.match(skill.read_text())
    assert match, "missing YAML frontmatter"
    meta = yaml.safe_load(match.group(1))
    name = meta.get("name")
    description = meta.get("description")
    assert isinstance(name, str)
    assert name.strip()
    assert name == skill.parent.name
    assert isinstance(description, str)
    assert description.strip()


@pytest.mark.parametrize("md", markdown_files, ids=_ids(markdown_files))
def test_no_relative_link_out_of_a_plugin(md: Path) -> None:
    plugin_root = PLUGINS / md.relative_to(PLUGINS).parts[0]
    for target in LINK.findall(md.read_text()):
        if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
            continue
        resolved = (md.parent / target.split("#")[0]).resolve()
        assert resolved.is_relative_to(plugin_root.resolve()), f"{target} leaves the plugin"
        assert resolved.exists(), f"{target} does not exist"
