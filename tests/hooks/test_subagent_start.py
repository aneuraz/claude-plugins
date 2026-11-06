from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "core"
SCRIPT = PLUGIN / "hooks" / "subagent_start.py"
BASE = (PLUGIN / "base.md").read_text(encoding="utf-8")
STDIN = '{"agent_id":"a1","agent_type":"general-purpose"}'
CAP = 10_000
REVIEW_HEADING = re.compile(r"^## .*independent review", re.IGNORECASE | re.MULTILINE)


def _load():
    spec = importlib.util.spec_from_file_location("subagent_start", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _context(output: str) -> str:
    return json.loads(output)["hookSpecificOutput"]["additionalContext"]


def test_base_md_has_the_review_section():
    assert REVIEW_HEADING.search(BASE)


def test_emits_base_md_without_the_review_section():
    out = _load().main(STDIN, {"CLAUDE_PLUGIN_ROOT": str(PLUGIN)})
    assert json.loads(out)["hookSpecificOutput"]["hookEventName"] == "SubagentStart"
    context = _context(out)
    assert context.startswith("# Base rules")
    assert not REVIEW_HEADING.search(context)
    assert "An independent review is a fresh agent" not in context
    assert len(context) < CAP


def test_other_sections_are_kept():
    context = _context(_load().main(STDIN, {"CLAUDE_PLUGIN_ROOT": str(PLUGIN)}))
    assert "## 4. Completion gate" in context
    assert "## 6. Writing: apply unslop" in context
    assert "## 7. Finding the rules" in context


def test_missing_review_section_keeps_everything(tmp_path):
    (tmp_path / "base.md").write_text("# Base rules\n\n## 1. A\n\ntext\n", encoding="utf-8")
    out = _load().main(STDIN, {"CLAUDE_PLUGIN_ROOT": str(tmp_path)})
    assert _context(out) == "# Base rules\n\n## 1. A\n\ntext\n"


def test_review_section_last_in_file(tmp_path):
    (tmp_path / "base.md").write_text(
        "# Base rules\n\n## 1. A\n\ntext\n\n## 2. Independent reviews\n\nask\n", encoding="utf-8"
    )
    out = _load().main(STDIN, {"CLAUDE_PLUGIN_ROOT": str(tmp_path)})
    assert _context(out) == "# Base rules\n\n## 1. A\n\ntext\n\n"


def test_internal_error_is_silent():
    assert _load().main(STDIN, {}) == ""


def _run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["uv", "run", "--no-project", "--python", "3.9", "python", str(SCRIPT)],  # noqa: S607
        input=STDIN,
        env={**env, "PATH": os.environ["PATH"]},
        capture_output=True,
        text=True,
        cwd=PLUGIN,
        timeout=120,
        check=False,
    )


@pytest.mark.parametrize("with_root", [True, False])
def test_runs_under_python_39(with_root):
    env = {"CLAUDE_PLUGIN_ROOT": str(PLUGIN)} if with_root else {}
    result = _run(env)
    assert result.returncode == 0
    if with_root:
        assert json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"] == "SubagentStart"
    else:
        assert result.stdout == ""
