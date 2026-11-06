"""PostToolUse hook on the Skill tool: restate the independent review at its three points."""

from __future__ import annotations

try:
    import json
    import sys
    from collections.abc import Mapping
    from typing import Final

    PREFIX = "superpowers:"

    _PLAN = (
        "Independent review: have a fresh agent review the plan, handed only the plan file "
        "and the spec it implements, never your conclusions, before executing it."
    )
    _TASKS_DONE = (
        "Independent review: once all of the plan's tasks are done, have a fresh agent review "
        "the branch's diff, handed only the diff and never your conclusions."
    )
    _DIFF = (
        "Independent review: before finishing, have a fresh agent review the branch's diff, "
        "handed only the diff and never your conclusions."
    )

    REVIEW_POINTS: Final[Mapping[str, str]] = {
        PREFIX + "brainstorming": (
            "Independent review: once the spec is written, have a fresh agent review the spec, "
            "handed only the spec file and never your conclusions."
        ),
        PREFIX + "writing-plans": _PLAN,
        PREFIX + "subagent-driven-development": _TASKS_DONE,
        PREFIX + "executing-plans": _TASKS_DONE,
        PREFIX + "finishing-a-development-branch": _DIFF,
    }

    def main(stdin: str) -> str:
        try:
            skill = json.loads(stdin)["tool_input"]["skill"]
            if not isinstance(skill, str):
                return ""
            name = skill if ":" in skill else PREFIX + skill
            reminder = REVIEW_POINTS.get(name)
            if reminder is None:
                return ""
            return json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": reminder,
                    }
                }
            )
        except Exception:
            return ""

    if __name__ == "__main__":
        sys.stdout.write(main(sys.stdin.read()))
except BaseException:  # a hook never fails a session
    raise SystemExit(0) from None
