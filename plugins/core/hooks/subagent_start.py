"""SubagentStart hook: inject base.md, without its independent-review section, into a subagent."""

from __future__ import annotations

try:
    import json
    import os
    import re
    import sys
    from pathlib import Path

    CONTEXT_CAP = 10_000
    REVIEW_HEADING = re.compile(r"^## .*independent review", re.IGNORECASE)
    HEADING = re.compile(r"^## ")

    def without_review_section(text):
        """Drop the section whose heading names independent reviews, up to the next section."""
        kept = []
        skipping = False
        for line in text.splitlines(keepends=True):
            if REVIEW_HEADING.match(line):
                skipping = True
            elif skipping and HEADING.match(line):
                skipping = False
            if not skipping:
                kept.append(line)
        return "".join(kept)

    def main(stdin, env):  # noqa: ARG001 - the hook input is not needed
        try:
            root = Path(env["CLAUDE_PLUGIN_ROOT"])
            context = without_review_section((root / "base.md").read_text(encoding="utf-8"))
            return json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SubagentStart",
                        "additionalContext": context[:CONTEXT_CAP],
                    }
                }
            )
        except Exception:
            return ""

    if __name__ == "__main__":
        sys.stdout.write(main(sys.stdin.read(), os.environ))
except BaseException:  # a hook never fails a subagent
    raise SystemExit(0) from None
