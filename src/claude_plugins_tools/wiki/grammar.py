"""The citations the lint reads: `wiki:` and `<pack>:<slug>` citations, and issue references.

Issue references follow `[repository]`: `name`'s issue and pull URLs, `<name's repo>#N` and
bare `#N` are rewritten into `issue_repository` and its `issue_reference` form (design §4).
"""

import re
from collections.abc import Callable
from typing import Final

from claude_plugins_tools.project import Project
from claude_plugins_tools.wiki.markdown import map_prose

WIKI_CITATION: Final = re.compile(r"wiki:(?P<directory>[a-z]+)/(?P<slug>[a-z0-9-]+)")
PACK_CITATION: Final = re.compile(
    r"(?<![\w/.:-])(?P<pack>rules-[a-z0-9]+(?:-[a-z0-9]+)*):(?P<slug>[a-z0-9]+(?:-[a-z0-9]+)*)"
)

_BARE_ISSUE: Final = re.compile(r"(?<![\w/#&-])#(\d+)\b")


def issue_rewriter(project: Project) -> Callable[[str], str] | None:
    """What makes every issue reference of a text the project's; None when not configured."""
    form = project.issue_reference
    if form is None:
        return None

    def reference(match: re.Match[str]) -> str:
        return form.replace("{n}", match[1])

    url = repo_ref = None
    if project.name:
        owner, _, repo = project.name.rpartition("/")
        prefix = rf"(?:{re.escape(owner)}/)?" if owner else ""
        repo_ref = re.compile(rf"(?<![\w-]){prefix}{re.escape(repo)}#(\d+)")
        if project.issue_repository and project.issue_repository != project.name:
            url = re.compile(rf"https://github\.com/{re.escape(project.name)}/(issues|pull)/(\d+)")
    target = f"https://github.com/{project.issue_repository}"

    def prose(text: str) -> str:
        if repo_ref is not None:
            text = repo_ref.sub(reference, text)
        return _BARE_ISSUE.sub(reference, text)

    def rewrite(text: str) -> str:
        """URLs anywhere, the rest in prose."""
        if url is not None:
            text = url.sub(lambda m: f"{target}/{m[1]}/{m[2]}", text)
        return map_prose(text, prose)

    return rewrite
