"""Entry point of the `cpt` command: `facts` and `wiki`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from claude_plugins_tools.facts import check, convert
from claude_plugins_tools.wiki import cli as wiki

#: argparse prefixes "usage: " itself.
USAGE = "cpt {facts,wiki} ..."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cpt", usage=USAGE)
    commands = parser.add_subparsers(dest="command")
    facts = commands.add_parser("facts", help="audit and run the fact-sets")
    check.build_parser(facts)
    facts_commands = facts.add_subparsers(dest="facts_command")
    report = facts_commands.add_parser("report", help="convert a runner's raw report")
    convert.build_parser(report)
    report.set_defaults(handler=convert.run)
    facts.set_defaults(handler=check.run)
    wiki_parser = commands.add_parser("wiki", help="index, check and search the wiki and packs")
    wiki.build_parser(wiki_parser)
    wiki_parser.set_defaults(handler=wiki.run)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    handler = getattr(args, "handler", None)
    if handler is None:
        print(f"usage: {USAGE}", file=sys.stderr)
        return 2
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
