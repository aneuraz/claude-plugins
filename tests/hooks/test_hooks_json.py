"""`plugins/core/hooks/hooks.json` wires each hook script to its event."""

from __future__ import annotations

import json
import re
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2] / "plugins" / "core"
HOOKS = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
#: How every hook runs: the plugin's own script, by `${CLAUDE_PLUGIN_ROOT}`.
_COMMAND = re.compile(r'python3 "\$\{CLAUDE_PLUGIN_ROOT\}/(hooks/[a-z_]+\.py)"')


def _commands(event: str) -> list[tuple[str | None, str]]:
    return [
        (entry.get("matcher"), hook["command"])
        for entry in HOOKS[event]
        for hook in entry["hooks"]
        if hook["type"] == "command"
    ]


def test_only_the_three_events() -> None:
    assert set(HOOKS) == {"SessionStart", "SubagentStart", "PostToolUse"}


def test_subagent_start_runs_subagent_start_py() -> None:
    assert _commands("SubagentStart") == [
        (None, 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/subagent_start.py"')
    ]


def test_session_start_runs_session_start_py() -> None:
    assert _commands("SessionStart") == [
        (None, 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/session_start.py"')
    ]


def test_post_tool_use_on_skill_runs_review_reminder_py() -> None:
    assert _commands("PostToolUse") == [
        ("Skill", 'python3 "${CLAUDE_PLUGIN_ROOT}/hooks/review_reminder.py"')
    ]


def test_every_command_names_an_existing_script() -> None:
    for event in HOOKS:
        for _, command in _commands(event):
            script = _COMMAND.fullmatch(command)
            assert script, command
            assert (PLUGIN / script[1]).is_file(), command
