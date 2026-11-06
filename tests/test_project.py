import re
from datetime import date
from pathlib import Path

import pytest

from claude_plugins_tools.project import IndexSection, Project, ProjectError, Surface, load_project

DOC = Path(__file__).parent.parent / "docs" / "project-toml.md"


def write(root: Path, text: str) -> None:
    (root / ".claude").mkdir()
    (root / ".claude" / "project.toml").write_text(text, encoding="utf-8")


def test_missing_file_is_unconfigured(tmp_path):
    assert load_project(tmp_path) == Project(root=tmp_path)
    assert load_project(tmp_path).wiki_path is None


def test_reads_candle_example(tmp_path):
    block = re.search(r"```toml\n(.*?)```", DOC.read_text(encoding="utf-8"), re.DOTALL)
    assert block
    write(tmp_path, block.group(1))
    project = load_project(tmp_path)
    assert project.name == "aneuraz/candle"
    assert project.siblings == ("aneuraz/candle-legacy", "aneuraz/candle-app")
    assert project.issue_reference == "candle-legacy#{n}"
    assert project.command == "uv run cpt"
    assert project.wiki_path == "docs/wiki"
    assert project.wiki_tooling == "cpt"
    assert project.archive_until == date(2026, 10, 12)
    assert project.archive_named == ("tests/contracts/test_wiki.py", "tests/helpers/wiki.py")
    assert project.index_sections[0] == IndexSection("Architecture decisions", "docs/adr", "*.md")
    assert len(project.index_sections) == 5
    assert project.project == "candle"
    assert project.up == "uv run python -m scripts.qa_stack up"
    assert project.variables == ("CANDLE_QA_CONFIG",)
    assert project.surfaces[0] == Surface(
        "cli",
        "uv run python -m scripts.qa_stack cli <candle command>",
        "candle as the agent identity",
    )
    assert project.work_dir == ".qa/current/work"
    assert project.up_keep is None
    assert project.errors_dir is None
    assert "scripts/qa_stack.py" in project.tooling_paths
    assert project.root == tmp_path


def test_malformed_names_key(tmp_path):
    write(tmp_path, '[repository]\nsiblings = "x"\n')
    with pytest.raises(ProjectError, match=r"repository\.siblings") as error:
        load_project(tmp_path)
    assert "project.toml" in str(error.value)


def test_unknown_key_refused(tmp_path):
    write(tmp_path, '[qa]\nlaunch = "x"\n')
    with pytest.raises(ProjectError, match=r"qa\.launch"):
        load_project(tmp_path)


def test_unknown_section_refused(tmp_path):
    write(tmp_path, "[nope]\na = 1\n")
    with pytest.raises(ProjectError, match="nope"):
        load_project(tmp_path)
