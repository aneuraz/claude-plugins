"""The cargo form of a check.

``cargo test -p <pkg> (--test <bin> | --lib) [--release] [-- <f1> ... <fn>]``.

Nothing else is accepted: a flag outside the grammar (``--exact``, ``--ignored``,
``--nocapture``, ``--features``, ...) changes which tests run, so the reports could no
longer prove what the check says. The grammar is parsed here; judging the entries is
`reports.red_tests`'s, and the static audit of the files is `cargo_fault`.

The audit finds a package's directory through ``cargo metadata`` (the workspace members'
manifest directories), never a fixed ``crates/<pkg>``.
"""

import json
import re
import shlex
import subprocess
from collections.abc import Callable, Iterable, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple

#: Maps a workspace member's name to the directory of its manifest.
type Members = Callable[[], Mapping[str, Path]]


class CargoCheck(NamedTuple):
    package: str
    #: The integration-test target, or None for ``--lib``.
    test: str | None
    release: bool
    filters: tuple[str, ...]

    @property
    def binary(self) -> str:
        """The nextest suite name: ``<pkg>`` for ``--lib``, else ``<pkg>::<bin>``."""
        return self.package if self.test is None else f"{self.package}::{self.test}"


def _flags(head: Sequence[str]) -> tuple[dict[str, str], set[str]] | str:
    """The valued (-p, --package, --test) and bare (--lib, --release) flags of the head,
    or the first token outside the grammar."""
    valued: dict[str, str] = {}
    bare: set[str] = set()
    it = iter(head)
    for arg in it:
        if arg in ("-p", "--package", "--test"):
            value = next(it, None)
            if value is None or value.startswith("-"):
                return f"{arg} without a name"
            valued["--test" if arg == "--test" else "-p"] = value
        elif arg in ("--lib", "--release"):
            bare.add(arg)
        else:
            return f"{arg} is outside the cargo form"
    return valued, bare


def parse(part: str) -> CargoCheck | str:
    """The `CargoCheck` a ``cargo test`` part names, or why it is outside the grammar."""
    try:
        tokens = shlex.split(part)
    except ValueError as error:
        return f"unparsable check {part!r}: {error}"
    if tokens[:2] != ["cargo", "test"]:
        return f"not a `cargo test` check: {part!r}"
    head, _, filters = _partition(tokens[2:])
    flags = _flags(head)
    if isinstance(flags, str):
        return f"{flags} in {part!r}"
    valued, bare = flags
    flag = next((f for f in filters if f.startswith("-")), None)
    if flag is not None:
        return f"{flag} is outside the cargo form in {part!r}"
    if "-p" not in valued or ("--lib" in bare) == ("--test" in valued):
        return f"-p <package> and exactly one of --test <bin> and --lib are required in {part!r}"
    return CargoCheck(valued["-p"], valued.get("--test"), "--release" in bare, tuple(filters))


def _partition(tokens: Sequence[str]) -> tuple[list[str], bool, list[str]]:
    if "--" not in tokens:
        return list(tokens), False, []
    at = list(tokens).index("--")
    return list(tokens[:at]), True, list(tokens[at + 1 :])


def shape(check: CargoCheck) -> str:
    """The check with its filters removed and its flags in one order: what a declared
    cargo form is matched against (``cargo test -p * --test * [--release]``)."""
    target = "--lib" if check.test is None else f"--test {check.test}"
    return f"cargo test -p {check.package} {target}" + (" --release" if check.release else "")


def select(
    check: CargoCheck, jobs: Mapping[str, Iterable[tuple[str, str]]]
) -> list[tuple[str | None, list[tuple[str, str, str]]]]:
    """For each filter (None when there is none), the (job, id, title) triples it selects.

    `jobs` maps a report's job to its (id, title) pairs, already restricted to the check's
    binary and profile; a filter selects the entries whose test path contains it, as
    libtest without ``--exact``.
    """
    flat = [(job, i, t) for job, entries in jobs.items() for i, t in entries]
    if not check.filters:
        return [(None, flat)]
    return [(f, [e for e in flat if f in e[2]]) for f in check.filters]


def _literal(filter_: str) -> str:
    """What a source file must contain for the filter to select something: a path filter
    is checked by its last segment."""
    return filter_.rstrip(":").rpartition("::")[2]


def cargo_fault(check: CargoCheck, members: Members) -> str | None:
    """Why the files of this cargo check cannot back it, or None."""
    directories = members()
    directory = directories.get(check.package)
    if directory is None:
        return f"{check.package} is not a workspace member"
    if check.test is None:
        sources = sorted((directory / "src").rglob("*.rs"))
        where = f"{check.package}'s src/"
        if not sources:
            return f"{where} holds no .rs file"
    else:
        candidates = (
            directory / "tests" / f"{check.test}.rs",
            directory / "tests" / check.test / "main.rs",
        )
        sources = [path for path in candidates if path.is_file()]
        where = f"tests/{check.test}.rs of {check.package}"
        if not sources:
            return f"{where} does not exist"
    text = "\n".join(path.read_text("utf-8") for path in sources)
    for filter_ in check.filters:
        literal = _literal(filter_)
        if not literal or not re.search(re.escape(literal), text):
            return f"filter {filter_!r} appears nowhere in {where}"
    return None


def workspace_members(root: Path) -> dict[str, Path]:
    """The workspace members of the cargo project at `root`, from ``cargo metadata``."""
    result = subprocess.run(  # noqa: S603, S607 — a fixed argv, no shell
        ["cargo", "metadata", "--format-version", "1", "--no-deps", "--offline"],  # noqa: S607
        capture_output=True,
        check=False,
        cwd=root,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cargo metadata failed: {result.stderr.strip()}")
    metadata = json.loads(result.stdout)
    ids = set(metadata["workspace_members"])
    return {
        package["name"]: Path(package["manifest_path"]).parent
        for package in metadata["packages"]
        if package["id"] in ids
    }
