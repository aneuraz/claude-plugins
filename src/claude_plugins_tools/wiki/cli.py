"""`cpt wiki index|check|search|show`: the options and the dispatch."""

import argparse
import sys
from pathlib import Path

from claude_plugins_tools.packs import enabled_packs, load_packs
from claude_plugins_tools.project import Project, ProjectError, load_project
from claude_plugins_tools.wiki.check import RULES, lint
from claude_plugins_tools.wiki.errors import WikiError
from claude_plugins_tools.wiki.index import index_path, render_index
from claude_plugins_tools.wiki.search import search, show


def _index(project: Project, _: argparse.Namespace) -> int:
    path = project.root / index_path(project)
    if project.wiki_tooling == "none":
        raise WikiError('[wiki] tooling is "none": this wiki\'s index is kept by hand')
    path.write_text(render_index(project), encoding="utf-8")
    return 0


def _check(project: Project, args: argparse.Namespace) -> int:
    faults, notices = lint(project, args.base, load_packs())
    for item in [*notices, *faults]:
        print(item)
    print(f"✗ {len(faults)} fault(s)" if faults else "✓ the wiki passes its lint")
    return 1 if faults else 0


def _search(project: Project, args: argparse.Namespace) -> int:
    if project.wiki_path is None:
        print("no [wiki] in .claude/project.toml: searching the packs only", file=sys.stderr)
    packs, note = enabled_packs(project.root, load_packs())
    if note:
        print(note, file=sys.stderr)
    hits = search(project, args.terms, packs)
    for hit in hits:
        print(hit)
    if not hits:
        print(f"no page or rule matches: {' '.join(args.terms)}")
    return 0


def _show(project: Project, args: argparse.Namespace) -> int:
    text, notice = show(project, args.citation, load_packs())
    if notice:
        print(notice, file=sys.stderr)
    print(text, end="")
    return 0


def build_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """The wiki subcommands, on the `wiki` subparser of `cpt`."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--root", type=Path, default=Path(), metavar="DIR", help="project root (default: .)"
    )
    commands = parser.add_subparsers(dest="wiki_command", required=True)
    commands.add_parser("index", parents=[common], help="write the wiki's index.md").set_defaults(
        wiki=_index
    )
    lint_parser = commands.add_parser(
        "check",
        parents=[common],
        help="run the lint",
        description="Run the lint. Each fault names the file, the line and the rule it breaks:\n"
        + "\n".join(f"  rule {n}: {rule}" for n, rule in RULES.items()),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    lint_parser.add_argument(
        "--base", default="origin/main", help="the branch whose log.md is append-only (rule 10)"
    )
    lint_parser.set_defaults(wiki=_check)
    found = commands.add_parser(
        "search",
        parents=[common],
        help="list the wiki pages and pack rules matching any term, most terms first",
    )
    found.add_argument("terms", nargs="+", metavar="TERM")
    found.set_defaults(wiki=_search)
    shown = commands.add_parser(
        "show", parents=[common], help="print a wiki page or a pack rule by its citation"
    )
    shown.add_argument("citation", metavar="CITATION", help="wiki:<dir>/<slug> or <pack>:<slug>")
    shown.set_defaults(wiki=_show)
    return parser


def run(args: argparse.Namespace) -> int:
    try:
        return args.wiki(load_project(args.root), args)
    except (WikiError, ProjectError) as error:
        print(f"✗ {error}", file=sys.stderr)
        return 1
