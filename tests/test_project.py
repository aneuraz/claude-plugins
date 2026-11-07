import re
from datetime import date
from pathlib import Path

import pytest

from claude_plugins_tools.project import (
    FactSchema,
    IndexSection,
    Project,
    ProjectError,
    Surface,
    load_project,
)

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
    assert project.index_sections[0] == IndexSection(
        "Architecture decisions", "docs/adr", "*.md", "headings"
    )
    assert project.index_sections[1].kind == "files"
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
    assert project.check_forms == (
        "uv run --all-packages --exact pytest -v",
        "uv run --all-packages --exact pytest -m integration -v",
        "uv run --package * --exact pytest -v",
        "uv run --package * --exact pytest -m integration -v",
    )
    assert project.root == tmp_path


def test_check_forms_absent_or_refused(tmp_path):
    assert load_project(tmp_path).check_forms is None
    write(tmp_path, '[facts]\ncheck_forms = "uv run pytest -v"\n')
    with pytest.raises(ProjectError, match=r"facts\.check_forms"):
        load_project(tmp_path)


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


def test_index_section_kind_defaults_to_files(tmp_path):
    write(tmp_path, '[[wiki.index_sections]]\ntitle = "Plans"\ndir = "docs/plans"\nglob = "*.md"\n')
    assert load_project(tmp_path).index_sections == (IndexSection("Plans", "docs/plans", "*.md"),)
    assert load_project(tmp_path).index_sections[0].kind == "files"


@pytest.mark.parametrize("extra", ['kind = "titles"', 'other = "x"'])
def test_index_section_refuses_an_unknown_kind_or_key(tmp_path, extra):
    section = '[[wiki.index_sections]]\ntitle = "P"\ndir = "d"\nglob = "*.md"\n'
    write(tmp_path, section + extra + "\n")
    with pytest.raises(ProjectError, match="index_sections"):
        load_project(tmp_path)


def test_check_forms_sub_table(tmp_path):
    write(
        tmp_path,
        '[facts.check_forms]\npytest = ["uv run pytest -v"]\n'
        "vitest = ['pnpm exec vitest run <file> -t \"<id>\"']\n"
        'playwright = ["a"]\nvitest-files = ["b"]\ncargo = ["c"]\nswift = ["d"]\n',
    )
    project = load_project(tmp_path)
    assert project.check_forms == ("uv run pytest -v",)
    assert project.runner_forms == {
        "vitest": ('pnpm exec vitest run <file> -t "<id>"',),
        "playwright": ("a",),
        "vitest-files": ("b",),
        "cargo": ("c",),
        "swift": ("d",),
    }


def test_flat_check_forms_leave_no_runner_forms(tmp_path):
    write(tmp_path, '[facts]\ncheck_forms = ["uv run pytest -v"]\n')
    project = load_project(tmp_path)
    assert project.check_forms == ("uv run pytest -v",)
    assert project.runner_forms == {}


@pytest.mark.parametrize(
    "body",
    ['golang = ["x"]', 'vitest = "x"', "vitest = [1]"],
)
def test_check_forms_sub_table_refuses_a_bad_entry(tmp_path, body):
    write(tmp_path, f"[facts.check_forms]\n{body}\n")
    with pytest.raises(ProjectError, match=r"facts\.check_forms"):
        load_project(tmp_path)


def test_facts_options_orphans_owner_and_schema(tmp_path):
    write(
        tmp_path,
        '[facts]\norphans = "facts-lines"\nowner = true\n'
        '[facts.schema]\nallowed = ["id", "timeout"]\nrequired = ["id"]\nstatuses = ["@spec"]\n',
    )
    project = load_project(tmp_path)
    assert (project.orphans, project.owner) == ("facts-lines", True)
    assert project.schema == FactSchema(("id", "timeout"), ("id",), ("@spec",))
    assert load_project(tmp_path.parent).orphans == "design-text"


@pytest.mark.parametrize(
    "text",
    [
        '[facts]\norphans = "elsewhere"\n',
        '[facts]\nowner = "yes"\n',
        "[facts.schema]\nallowd = []\n",
        "[facts.schema]\nallowed = 3\n",
    ],
)
def test_facts_options_refuse_bad_values(tmp_path, text):
    write(tmp_path, text)
    with pytest.raises(ProjectError):
        load_project(tmp_path)
