"""The packs the package carries: their rules, and how a `<pack>:<slug>` citation resolves."""

from pathlib import Path

import pytest

from claude_plugins_tools import packs as packs_module
from claude_plugins_tools.packs import Rule, UnknownCitation, load_packs, resolve
from tests.wiki.helpers import rule, write, write_pack

ROOT = Path(__file__).resolve().parent.parent


def _fixture(root: Path) -> None:
    write_pack(
        root,
        "rules-security",
        {
            "parameterised-sql": rule("Parameterised SQL", "Bind every value.\n"),
            "no-string-sql": rule("No string SQL", superseded_by="parameterised-sql"),
            "dangling": rule("Dangling", superseded_by="gone"),
        },
    )
    # Not a rule: a pack's non-rule files sit beside rules/, never under it.
    write(root, {"plugins/rules-security/skills/rules-security/SKILL.md": "# skill\n"})
    write(root, {"plugins/core/skills/qa/rules/not-a-pack.md": rule("Not a pack")})


def test_load_packs_reads_rules_from_a_root(tmp_path: Path) -> None:
    _fixture(tmp_path)
    packs = load_packs(tmp_path)
    assert list(packs) == ["rules-security"]
    base = tmp_path / "plugins/rules-security/skills/rules-security/rules"
    assert packs["rules-security"].rules["no-string-sql"] == Rule(
        "no-string-sql", "No string SQL", base / "no-string-sql.md", "parameterised-sql"
    )
    assert packs["rules-security"].rules["parameterised-sql"].superseded_by is None


def test_resolve_follows_superseded_by_once(tmp_path: Path) -> None:
    _fixture(tmp_path)
    packs = load_packs(tmp_path)
    assert resolve("rules-security:parameterised-sql", packs).slug == "parameterised-sql"
    assert resolve("rules-security:no-string-sql", packs).slug == "parameterised-sql"


@pytest.mark.parametrize(
    "citation",
    ["rules-security:nowhere", "rules-nowhere:parameterised-sql", "rules-security:dangling", "x"],
)
def test_resolve_refuses_an_unknown_citation(tmp_path: Path, citation: str) -> None:
    _fixture(tmp_path)
    with pytest.raises(UnknownCitation, match=citation):
        resolve(citation, load_packs(tmp_path))


def test_bundled_packs_fall_back_to_the_source_checkout() -> None:
    # Run from this repository, the wheel's force-included plugins/ is not under src/.
    bundled = load_packs()
    assert bundled.keys() == load_packs(ROOT).keys()
    assert "rules-python" in bundled
    assert bundled["rules-python"].rules["icontract-contracts"].path.is_relative_to(ROOT)


def test_bundled_packs_come_from_the_package_when_installed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # An installed wheel carries the packs as claude_plugins_tools/plugins.
    package = tmp_path / "claude_plugins_tools"
    write_pack(package, "rules-installed", {"a-rule": rule("A rule")})
    monkeypatch.setattr(packs_module.resources, "files", lambda _: package)
    assert list(load_packs()) == ["rules-installed"]
