"""The whole-file vitest form: the project's own command, naming test files.

``[facts.check_forms] vitest-files = ['npm --prefix app test -- <files>']`` declares it
(`capture`'s). A check in that form is the form's tokens before ``<files>`` (``*`` stands
for any one token), one or more files or directories, the form's tokens after ``<files>``,
and optionally ``-t <regex>`` (or ``--testNamePattern``). The files are relative to the
directory the command prefix names (``--prefix``, ``-C``, ``--dir`` or ``--cwd``; else the
repository root); a report entry's ``file`` is relative to the repository, so the check's
``src/a.test.ts`` under ``--prefix app`` selects the entries of ``app/src/a.test.ts``, and a
directory selects the entries beneath it.

``-t`` is a regular expression searched in the entry's full name: its ancestor titles and
its title joined by single spaces, the file's name not included. That is vitest's own rule:
``getTaskFullName`` in ``@vitest/runner`` (``chunk-artifact.js``, 4.1.11) builds the name,
and ``interpretTaskModes`` skips a test whose full name does not ``.match`` the pattern.
Python's ``re`` stands in for JavaScript's; the syntax the two share is what a pattern
should use.

A fact is green when the check selects at least one entry and every selected entry passed.
"""

import posixpath
import re
import shlex
from collections.abc import Sequence
from pathlib import Path
from typing import Literal, NamedTuple

PATTERN_TOKENS = 2
PATTERN_FLAGS = ("-t", "--testNamePattern")
DIRECTORY_FLAGS = ("--prefix", "-C", "--dir", "--cwd")


class Selection(NamedTuple):
    #: Where the command runs, relative to the repository ("" for the root).
    directory: str
    #: The files and directories named, relative to `directory`.
    files: tuple[str, ...]
    pattern: str | None


def _directory(head: Sequence[str]) -> str:
    for flag, value in zip(head, head[1:], strict=False):
        if flag in DIRECTORY_FLAGS:
            directory = posixpath.normpath(value)
            return "" if directory == "." else directory
    return ""


def _fits(want: Sequence[str], tokens: Sequence[str]) -> bool:
    return len(want) == len(tokens) and all(
        w in ("*", t) for w, t in zip(want, tokens, strict=True)
    )


def _pattern(rest: Sequence[str]) -> str | None | Literal[False]:
    """The `-t` pattern the remaining tokens give, None when they are none, False when
    they are anything else."""
    if not rest:
        return None
    if len(rest) == PATTERN_TOKENS and rest[0] in PATTERN_FLAGS:
        return rest[1]
    return False


def _parse_with(check: str, tokens: Sequence[str], form: str) -> Selection | str | None:
    want = shlex.split(form)
    if "<files>" not in want:
        return None
    at = want.index("<files>")
    head, tail = want[:at], want[at + 1 :]
    if not _fits(head, tokens[: len(head)]):
        return None
    rest = tokens[len(head) :]
    count = next((i for i, token in enumerate(rest) if token.startswith("-")), len(rest))
    files, rest = rest[:count], rest[count:]
    if not files:
        return f"{check!r} names no test file"
    pattern = _pattern(rest[len(tail) :])
    if not _fits(tail, rest[: len(tail)]) or pattern is False:
        return f"a token outside the check's form in {check!r}"
    return Selection(_directory(head), tuple(files), pattern)


def parse(check: str, forms: Sequence[str] | None) -> Selection | str | None:
    """None when `check` is not in a declared whole-file form, a fault message when it
    starts like one and then goes wrong, else what it selects."""
    try:
        tokens = shlex.split(check)
    except ValueError:
        return None
    faults = []
    for form in forms or ():
        found = _parse_with(check, tokens, form)
        if isinstance(found, Selection):
            return found
        if found is not None:
            faults.append(found)
    return faults[0] if faults else None


def fault(selection: Selection, root: Path) -> str | None:
    """Why this selection cannot be trusted, or None: each name an existing file or
    directory, the pattern a regular expression."""
    for name in selection.files:
        if not (root / selection.directory / name).exists():
            return f"{posixpath.join(selection.directory, name)} does not exist"
    if selection.pattern is not None:
        try:
            re.compile(selection.pattern)
        except re.error as error:
            return f"{selection.pattern!r} is not a regular expression: {error}"
    return None


def full_name(id_: str, title: str, file: str | None) -> str:
    """The name vitest matches `-t` against: ancestors and title joined by spaces. A
    normalized entry's id is ``<file>::<ancestor> > … > <title>``."""
    rest = id_[len(file) + 2 :] if file and id_.startswith(f"{file}::") else title
    if not rest.endswith(title):
        return title
    ancestors = rest[: len(rest) - len(title)].removesuffix(" > ")
    return f"{ancestors.replace(' > ', ' ')} {title}" if ancestors else title


def selects(selection: Selection, id_: str, title: str, file: str | None) -> bool:
    """Whether the entry is one the check runs."""
    if file is None:
        return False
    if not any(
        file == path or file.startswith(path + "/")
        for path in (
            posixpath.normpath(posixpath.join(selection.directory, name))
            for name in selection.files
        )
    ):
        return False
    if selection.pattern is None:
        return True
    try:
        return re.search(selection.pattern, full_name(id_, title, file)) is not None
    except re.error:
        return False
