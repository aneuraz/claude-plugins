"""What a fact's check names, and whether it is a form the project declares.

A check is a selector: it names, in its runner's own syntax, the tests that prove
its fact. This module audits it statically, in every mode, because running it (or
reading the reports) cannot reveal a fault in it:

* pytest: ``file::function`` selectors, each naming one definition; the rest of the
  check is one of the project's ``check_forms``;
* vitest and Playwright by id: ``pnpm exec vitest run <file> -t "<ID>"`` and
  ``pnpm exec playwright test <file> -g "<ID>"`` when the project declares those forms
  under ``[facts.check_forms]``; the id is the fact's own and at least one test of the
  file carries it. Without a declared form, the legacy ``pnpm -C agent exec`` form is
  audited under ``--vitest-root``.

A form is a command line in which ``*`` stands for any one token, ``<file>`` for the
test file and ``<id>`` for the fact id (the by-id forms).
"""

import re
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path

from claude_plugins_tools.facts import cargo

DEFAULT_VITEST_ROOT = "agent"
SELECTOR_PATTERN = re.compile(r"(\S+\.py)::(\w+)(\[[^\s\]]*\])?")
AGENT_SELECTOR_PATTERN = re.compile(
    r"pnpm -C agent exec (?:vitest run|playwright test) (\S+\.ts) -[tg] \"([A-Z]{2,4}-\d{3})\""
)
RUNNERS = ("pytest", "vitest", "playwright", "cargo", "swift")
#: The runners with a by-id form: the file and the id are read from the check.
BY_ID_RUNNERS = ("vitest", "playwright")


def split_parts(check: str) -> list[str]:
    """The `&&`-joined parts of a check; an `&&` inside quotes is not a separator."""
    parts, current, quote = [], "", ""
    i = 0
    while i < len(check):
        char = check[i]
        if quote:
            quote = "" if char == quote else quote
        elif char in "\"'":
            quote = char
        elif check.startswith("&&", i):
            parts.append(current.strip())
            current, i = "", i + 2
            continue
        current += char
        i += 1
    parts.append(current.strip())
    return parts


def runner_of(check: str) -> str:
    """The tool this check invokes, for --runner filtering.

    Matched against argv tokens, not the raw string: a path or flag that
    happens to contain "pytest" as a substring must not be mistaken for the
    token that names the runner.
    """
    try:
        tokens = set(shlex.split(check))
    except ValueError:
        return "unknown"
    for runner in RUNNERS:
        if runner in tokens:
            return runner
    return "unknown"


def _by_id_match(check: str, forms: Sequence[str]) -> tuple[str, str] | None:
    """The (file, id) this check names when its tokens are one of the by-id `forms`."""
    try:
        tokens = shlex.split(check)
    except ValueError:
        return None
    for form in map(shlex.split, forms):
        if len(form) != len(tokens):
            continue
        found: dict[str, str] = {}
        for want, token in zip(form, tokens, strict=True):
            if want in ("<file>", "<id>"):
                found[want] = token
            elif want not in ("*", token):
                break
        else:
            if "<file>" in found and "<id>" in found:
                return found["<file>"], found["<id>"]
    return None


def by_id_selector(
    check: str, runner_forms: Mapping[str, Sequence[str]] | None
) -> tuple[str, str] | None:
    """The (file, id) of a vitest/Playwright check in a declared by-id form, else None."""
    runner = runner_of(check)
    if not runner_forms or runner not in BY_ID_RUNNERS or runner not in runner_forms:
        return None
    return _by_id_match(check, runner_forms[runner])


def _by_id_fault(check: str, root: Path, forms: Sequence[str], fact_id: str | None) -> str | None:
    """Why this by-id check cannot be trusted, or None. Its id must be the fact's own:
    another id would gate the fact on another fact's tests. Its file must exist and
    hold at least one test whose title starts with the id: a typo in either would
    otherwise surface only as `not run`, once the fact is gated."""
    selector = _by_id_match(check, forms)
    if selector is None:
        return f"a token outside the check's form in {check!r}"
    file, check_id = selector
    if fact_id is not None and check_id != fact_id:
        return f"{check_id} is not {fact_id}"
    path = root / file
    if not path.is_file():
        return f"{file} does not exist"
    pattern = rf"\b(?:it|test)\(\s*[\"'`]{re.escape(check_id)} "
    if not re.search(pattern, path.read_text("utf-8")):
        return f"no test of {file} has a title starting with {check_id}"
    return None


def _agent_selector_fault(
    agent_match: re.Match[str], root: Path, vitest_root: str = DEFAULT_VITEST_ROOT
) -> str | None:
    """Why this agent (vitest/Playwright) selector cannot be trusted, or None."""
    path, fact_id = root / vitest_root / agent_match.group(1), agent_match.group(2)
    if not path.exists():
        return f"{vitest_root}/{agent_match.group(1)} does not exist"
    pattern = rf"\b(?:it|test)\(\s*[\"'`]{re.escape(fact_id)} "
    count = len(re.findall(pattern, path.read_text("utf-8")))
    where = f"{vitest_root}/{agent_match.group(1)}"
    return None if count == 1 else f"{fact_id} names {count} tests in {where}"


def _form_fault(check: str, forms: Sequence[str]) -> str | None:
    """Why this pytest check leaves every one of `forms`, or None.

    The gate reads only a check's selectors, so any other token (a -k, a -p,
    a shell operator) would make the command differ from what the reports
    prove. A check is in a form when its tokens, its selectors removed, are
    the form's tokens, where a `*` token stands for any one token (the member
    a `--package` names, say).
    """
    rest = [token for token in shlex.split(check) if not SELECTOR_PATTERN.fullmatch(token)]
    for form in map(shlex.split, forms):
        if len(form) == len(rest) and all(f in ("*", t) for f, t in zip(form, rest, strict=True)):
            return None
    return f"a token outside the check's form in {check!r}"


def _python_selector_fault(check: str, root: Path, forms: Sequence[str] | None) -> str | None:
    """Why this file::function check cannot be trusted, or None; a pytest check
    must also take one of `forms` when they are given (`[facts] check_forms`)."""
    if forms is not None and runner_of(check) == "pytest":
        form = _form_fault(check, forms)
        if form is not None:
            return form
    matches = list(SELECTOR_PATTERN.finditer(check))
    if not matches:
        return f"no file::function selector in {check!r}"
    for match in matches:
        path, function = root / match.group(1), match.group(2)
        if not path.exists():
            return f"{match.group(1)} does not exist"
        definitions = len(
            re.findall(rf"^(?:async )?def {re.escape(function)}\(", path.read_text("utf-8"), re.M)
        )
        if definitions != 1:
            return f"{function} is defined {definitions} times in {match.group(1)}"
    return None


def _part_fault(  # noqa: PLR0913 — one knob per audit the caller configures
    check: str,
    root: Path,
    vitest_root: str = DEFAULT_VITEST_ROOT,
    forms: Sequence[str] | None = None,
    *,
    runner_forms: Mapping[str, Sequence[str]] | None = None,
    fact_id: str | None = None,
    members: cargo.Members | None = None,
) -> str | None:
    """Why this part's selector cannot be trusted, or None.

    A selector must name exactly one definition. Two functions of the same
    name in one file make pytest report "collected 1 item" and run the second
    one, so a check can execute a test other than the one it names and still
    report green; ruff's F811 is what reveals it. Running the check cannot
    catch this, since it is the wrong test that passes.

    Every selector of the check, not the first: a check may name several tests,
    and validating only the first would leave an emptied redefinition of a later
    one with the fact still printing green.

    A check whose runner is not one of RUNNERS is a fault on its own: nothing
    downstream would ever select it to run, so a typo here is silent forever.
    """
    runner = runner_of(check)
    if runner == "unknown":
        return f"unknown runner in {check!r}"
    declared = (runner_forms or {}).get(runner)
    if runner == "cargo":
        return _cargo_fault(check, declared, members)
    if runner == "swift":
        return _swift_fault(check, declared)
    if runner in BY_ID_RUNNERS and declared:
        return _by_id_fault(check, root, declared, fact_id)
    agent_match = AGENT_SELECTOR_PATTERN.search(check)
    if agent_match:
        return _agent_selector_fault(agent_match, root, vitest_root)
    return _python_selector_fault(check, root, forms)


def _tokens_fault(check: str, tokens: Sequence[str], forms: Sequence[str]) -> str | None:
    for form in map(shlex.split, forms):
        if len(form) == len(tokens) and all(
            f in ("*", t) for f, t in zip(form, tokens, strict=True)
        ):
            return None
    return f"a token outside the check's form in {check!r}"


def _cargo_fault(
    check: str, forms: Sequence[str] | None, members: cargo.Members | None
) -> str | None:
    """The grammar of cargo.py, the declared `cargo` forms when there are some (matched
    on the part with its filters removed), then the files `cargo metadata` locates."""
    parsed = cargo.parse(check)
    if isinstance(parsed, str):
        return parsed
    if forms:
        fault = _tokens_fault(check, shlex.split(cargo.shape(parsed)), forms)
        if fault is not None:
            return fault
    if members is None:
        return None
    try:
        return cargo.cargo_fault(parsed, members)
    except (RuntimeError, OSError, ValueError, KeyError) as error:
        return f"cannot audit {check!r}: {error}"


def _swift_fault(check: str, forms: Sequence[str] | None) -> str | None:
    """A swift check is audited for its form only, and never judged: no report holds it."""
    if not forms:
        return f"no swift form is declared for {check!r} ([facts.check_forms] swift)"
    try:
        return _tokens_fault(check, shlex.split(check), forms)
    except ValueError as error:
        return f"unparsable check {check!r}: {error}"


def selector_fault(  # noqa: PLR0913 — one knob per audit the caller configures
    check: str,
    root: Path,
    vitest_root: str = DEFAULT_VITEST_ROOT,
    forms: Sequence[str] | None = None,
    *,
    runner_forms: Mapping[str, Sequence[str]] | None = None,
    fact_id: str | None = None,
    members: cargo.Members | None = None,
) -> str | None:
    """Why this check's selectors cannot be trusted, or None: the first fault of its
    `&&`-joined parts, each audited on its own (see `_part_fault`)."""
    for part in split_parts(check):
        if not part:
            return f"an empty part in {check!r}"
        fault = _part_fault(
            part,
            root,
            vitest_root,
            forms,
            runner_forms=runner_forms,
            fact_id=fact_id,
            members=members,
        )
        if fault is not None:
            return fault
    return None
