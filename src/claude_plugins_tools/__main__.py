"""Entry point of the `cpt` command (subcommands arrive with later tasks)."""

from __future__ import annotations

import sys

USAGE = "usage: cpt {facts,wiki} ...\n(not implemented yet)"


def main() -> int:
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
