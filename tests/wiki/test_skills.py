"""The plugins name only `cpt` subcommands that exist (port of candle's
tests/contracts/test_wiki_skills.py::test_skills_name_only_existing_subcommands)."""

import re
from pathlib import Path

import pytest

from claude_plugins_tools.__main__ import main

PLUGINS = Path(__file__).resolve().parents[2] / "plugins"
#: A command named in code: `wiki <subcommand> …` or `facts …`, optionally after `cpt `.
_COMMAND = re.compile(r"`(?:cpt )?(wiki [a-z][a-z-]*|facts)(?=[\s`])")


def _texts() -> list[Path]:
    return [PLUGINS / "core" / "base.md", *sorted(PLUGINS.glob("*/skills/**/*.md"))]


def test_skills_name_only_existing_subcommands(capsys: pytest.CaptureFixture[str]) -> None:
    named = {
        match[1]
        for path in _texts()
        for match in _COMMAND.finditer(path.read_text(encoding="utf-8"))
    }
    assert {"wiki index", "wiki check", "wiki search", "wiki show", "facts"} <= named
    undefined = []
    for command in sorted(named):
        with pytest.raises(SystemExit) as stopped:
            main([*command.split(), "--help"])
        if stopped.value.code != 0:
            undefined.append(command)
    capsys.readouterr()
    assert undefined == []
