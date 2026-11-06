from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "core"
SCRIPT = PLUGIN / "hooks" / "review_reminder.py"


def _load():
    spec = importlib.util.spec_from_file_location("review_reminder", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _stdin(skill: str | None) -> str:
    # Shape measured with claude -p: tool_name "Skill", tool_input {"skill": "<plugin:name>"}.
    tool_input = {} if skill is None else {"skill": skill}
    return json.dumps(
        {"hook_event_name": "PostToolUse", "tool_name": "Skill", "tool_input": tool_input}
    )


def _context(output: str) -> str:
    payload = json.loads(output)["hookSpecificOutput"]
    assert payload["hookEventName"] == "PostToolUse"
    return payload["additionalContext"]


def test_reminds_after_writing_plans():
    text = _context(_load().main(_stdin("superpowers:writing-plans")))
    assert "independent review" in text.lower()
    assert "plan" in text
    assert "fresh agent" in text


@pytest.mark.parametrize(
    ("skill", "artefact"),
    [
        ("superpowers:brainstorming", "spec"),
        ("superpowers:subagent-driven-development", "diff"),
        ("superpowers:executing-plans", "diff"),
        ("superpowers:finishing-a-development-branch", "diff"),
    ],
)
def test_reminds_for_each_point(skill, artefact):
    text = _context(_load().main(_stdin(skill)))
    assert "fresh agent" in text
    assert artefact in text
    assert "conclusions" in text


def test_silent_for_other_skills():
    assert _load().main(_stdin("core:unslop")) == ""


def test_silent_without_skill_name():
    assert _load().main(_stdin(None)) == ""
    assert _load().main('{"tool_input": []}') == ""
    assert _load().main('{"tool_input": {"skill": 5}}') == ""


def test_silent_on_bad_json():
    assert _load().main("not json") == ""
    assert _load().main("") == ""


def test_bare_name_accepted():
    module = _load()
    assert module.main(_stdin("writing-plans")) == module.main(_stdin("superpowers:writing-plans"))
    assert module.main(_stdin("writing-plans")) != ""


def test_points_are_short_english():
    for text in _load().REVIEW_POINTS.values():
        assert len(text) < 400


def _run(stdin: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["uv", "run", "--no-project", "--python", "3.9", "python", str(SCRIPT)],  # noqa: S607
        input=stdin,
        env={"PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        cwd=PLUGIN,
        timeout=120,
        check=False,
    )


def test_runs_under_python_39():
    result = _run(_stdin("superpowers:writing-plans"))
    assert result.returncode == 0
    assert _context(result.stdout).startswith("Independent review")
    silent = _run("not json")
    assert silent.returncode == 0
    assert silent.stdout == ""
