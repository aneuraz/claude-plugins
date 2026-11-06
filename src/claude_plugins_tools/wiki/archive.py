"""Where old citations may stay: the archive set, outside rules 5 and 7.

`[wiki] archive_until` archives the dated specs and plans up to that date, and
`[wiki] archive_named` the files (or, ending in `/`, directories) it names. A project that sets
neither archives nothing: every tracked text file is checked.
"""

import re
import shutil
import subprocess
from datetime import date
from pathlib import Path
from typing import Final

from claude_plugins_tools.project import Project
from claude_plugins_tools.wiki.errors import WikiError

_DATED: Final = re.compile(r"^docs/superpowers/[^/]+/(\d{4})-(\d{2})-(\d{2})-[^/]+$")


def git(root: Path, *args: str) -> str:
    executable = shutil.which("git")
    if executable is None:
        raise WikiError("git is not on PATH")
    result = subprocess.run(  # noqa: S603 — a fixed argument list, no shell
        [executable, *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode != 0:
        raise WikiError(f"git {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout


def is_archived(path: str, project: Project) -> bool:
    named = project.archive_named
    if any(path == name or (name.endswith("/") and path.startswith(name)) for name in named):
        return True
    if project.archive_until is None:
        return False
    dated = _DATED.match(path)
    return bool(dated) and date(*map(int, dated.groups())) <= project.archive_until


def scanned_files(project: Project) -> list[tuple[str, str]]:
    """Every tracked text file outside the archive, with its text."""
    root = project.root
    found: list[tuple[str, str]] = []
    for path in git(root, "ls-files", "-z").split("\0"):
        if not path or is_archived(path, project):
            continue
        data = (root / path).read_bytes() if (root / path).is_file() else b""
        if b"\0" in data:
            continue
        try:
            found.append((path, data.decode("utf-8")))
        except UnicodeDecodeError:
            continue
    return found
