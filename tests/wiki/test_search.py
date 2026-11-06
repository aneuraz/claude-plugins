"""`cpt wiki search` and `cpt wiki show`: the project's wiki and the packs, by citation."""

import json
from pathlib import Path

import pytest

from claude_plugins_tools.__main__ import main
from claude_plugins_tools.packs import load_packs
from tests.wiki.helpers import clean_wiki, rule, write_pack


@pytest.fixture
def packs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Fixture packs under `tmp_path/packs`, served to the CLI in place of the bundled ones."""
    root = tmp_path / "packs"
    write_pack(
        root,
        "rules-security",
        {
            "parameterised-sql": rule("Parameterised SQL", "Bind every value; never pin SQL.\n"),
            "no-string-sql": rule("No string SQL pinned", superseded_by="parameterised-sql"),
        },
    )
    write_pack(root, "rules-python", {"no-eval": rule("No eval", "Never eval input.\n")})
    loaded = load_packs(root)
    monkeypatch.setattr("claude_plugins_tools.wiki.cli.load_packs", lambda: loaded)
    return root


def _run(capsys: pytest.CaptureFixture[str], *argv: str) -> tuple[int, str, str]:
    code = main(["wiki", *argv])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


def test_search_lists_wiki_pages_and_pack_rules(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    clean_wiki(repo)
    code, out, _ = _run(capsys, "search", "PIN", "--root", str(repo))
    assert code == 0
    assert out.splitlines() == [
        "wiki:hubs/notes  Notes",  # its body links "Pin every version"
        "wiki:rules/pin-every-version  Pin every version",
        "rules-security:parameterised-sql  Parameterised SQL",
    ]
    code, out, _ = _run(capsys, "search", "sql", "bind", "--root", str(repo))
    assert out.splitlines() == ["rules-security:parameterised-sql  Parameterised SQL"]


def test_search_without_project_toml(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(capsys, "search", "eval", "--root", str(tmp_path))
    assert code == 0
    assert out.splitlines() == ["rules-python:no-eval  No eval"]
    assert "no [wiki] in .claude/project.toml" in err


def test_search_without_a_hit_says_so(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = _run(capsys, "search", "nothing-matches-this", "--root", str(tmp_path))
    assert code == 0
    assert out.strip() == "no page or rule matches: nothing-matches-this"


def test_show_prints_a_rule(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, _ = _run(capsys, "show", "rules-python:no-eval", "--root", str(tmp_path))
    assert code == 0
    assert out == (packs / "plugins/rules-python/skills/rules-python/rules/no-eval.md").read_text(
        encoding="utf-8"
    )


def test_show_follows_a_superseded_rule(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code, out, err = _run(capsys, "show", "rules-security:no-string-sql", "--root", str(tmp_path))
    assert code == 0
    assert "Bind every value" in out
    assert "cite rules-security:parameterised-sql" in err


def test_show_prints_a_wiki_page(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    clean_wiki(repo)
    code, out, _ = _run(capsys, "show", "wiki:rules/pin-every-version", "--root", str(repo))
    assert code == 0
    assert "Always." in out


@pytest.mark.parametrize("citation", ["rules-python:nowhere", "wiki:rules/nowhere", "nonsense"])
def test_show_refuses_an_unknown_citation(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str], citation: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    clean_wiki(repo)
    code, out, err = _run(capsys, "show", citation, "--root", str(repo))
    assert (code, out) == (1, "")
    assert citation in err


def _settings(root: Path, enabled: dict[str, bool]) -> None:
    (root / ".claude").mkdir(parents=True, exist_ok=True)
    text = json.dumps({"enabledPlugins": enabled})
    (root / ".claude" / "settings.json").write_text(text, encoding="utf-8")


def test_search_covers_the_enabled_packs_only(
    tmp_path: Path, packs: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    _settings(
        tmp_path,
        {
            "rules-python@aneuraz-plugins": True,
            "rules-security@aneuraz-plugins": False,
            "rules-security@elsewhere": True,
            "core@aneuraz-plugins": True,
        },
    )
    code, out, err = _run(capsys, "search", "e", "--root", str(tmp_path))
    assert code == 0
    assert out.splitlines() == ["rules-python:no-eval  No eval"]
    assert "every bundled pack" not in err
    # show still resolves any bundled pack
    code, out, _ = _run(capsys, "show", "rules-security:parameterised-sql", "--root", str(tmp_path))
    assert code == 0
    assert "Bind every value" in out


@pytest.mark.parametrize("enabled", [None, {"core@aneuraz-plugins": True}])
def test_search_without_enabled_packs_covers_every_pack(
    tmp_path: Path,
    packs: Path,
    capsys: pytest.CaptureFixture[str],
    enabled: dict[str, bool] | None,
) -> None:
    if enabled is not None:
        _settings(tmp_path, enabled)
    code, out, err = _run(capsys, "search", "sql", "--root", str(tmp_path))
    assert code == 0
    assert out.splitlines() == ["rules-security:parameterised-sql  Parameterised SQL"]
    notes = [line for line in err.splitlines() if "every bundled pack" in line]
    assert len(notes) == 1
