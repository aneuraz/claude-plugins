from __future__ import annotations

import importlib.util
import json
import os
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PLUGIN = ROOT / "plugins" / "core"
SCRIPT = PLUGIN / "hooks" / "session_start.py"
BASE = (PLUGIN / "base.md").read_text(encoding="utf-8")
STDIN = '{"source":"startup"}'
CAP = 10_000
MARKET = "@datazard-plugins"


def _load():
    spec = importlib.util.spec_from_file_location("session_start", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _env(project: Path | None = None) -> dict[str, str]:
    env = {"CLAUDE_PLUGIN_ROOT": str(PLUGIN)}
    if project is not None:
        env["CLAUDE_PROJECT_DIR"] = str(project)
    return env


def _project(tmp_path: Path, packs: list[str]) -> Path:
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    settings = {"enabledPlugins": {name + MARKET: True for name in packs}}
    (project / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
    return project


def _context(output: str) -> str:
    return json.loads(output)["hookSpecificOutput"]["additionalContext"]


def test_base_md_fits():
    assert len(BASE) <= 6000


def test_emits_base_md():
    out = _load().main(STDIN, _env(), lambda _project: [])
    payload = json.loads(out)
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert _context(out).startswith(BASE)


def test_reports_missing_pack(tmp_path):
    project = _project(tmp_path, ["core", "rules-python"])
    entries = [
        {
            "id": "core" + MARKET,
            "scope": "project",
            "enabled": True,
            "projectPath": str(project),
            "projectEnabled": True,
        },
        {
            "id": "rules-python" + MARKET,
            "scope": "project",
            "enabled": True,
            "projectPath": str(tmp_path / "elsewhere"),
            "projectEnabled": True,
        },
    ]
    out = _load().main(STDIN, _env(project), lambda _project: entries)
    last = _context(out).splitlines()[-1]
    assert "rules-python" + MARKET in last
    assert "core" + MARKET not in last
    assert "not loaded" in last


def test_user_scope_counts_everywhere(tmp_path):
    project = _project(tmp_path, ["rules-python"])
    entries = [{"id": "rules-python" + MARKET, "scope": "user", "enabled": True}]
    out = _load().main(STDIN, _env(project), lambda _project: entries)
    assert _context(out).startswith(BASE)
    assert "not loaded" not in _context(out)


def test_lister_unavailable(tmp_path):
    project = _project(tmp_path, ["rules-python"])
    out = _load().main(STDIN, _env(project), lambda _project: None)
    assert "not loaded" not in _context(out)
    assert _context(out).startswith(BASE)


@pytest.mark.parametrize(
    "entry",
    [
        {"id": ["x"], "enabled": True, "scope": "user"},
        {"id": "x" + MARKET, "enabled": True, "scope": "project", "projectPath": 5},
    ],
)
def test_malformed_entry_keeps_base_md(tmp_path, entry):
    project = _project(tmp_path, ["rules-python"])
    out = _load().main(STDIN, _env(project), lambda _project: [entry])
    assert _context(out).startswith(BASE)
    assert "not loaded" not in _context(out)


def test_context_stays_under_cap(tmp_path):
    packs = [f"rules-p{i}" for i in range(7)]
    project = _project(tmp_path, packs)
    out = _load().main(STDIN, _env(project), lambda _project: [])
    assert len(_context(out)) < CAP


def test_internal_error_is_silent():
    assert _load().main(STDIN, {}, lambda _project: []) == ""


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
        assert json.loads(result.stdout)["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    else:
        assert result.stdout == ""
