"""SessionStart hook: inject base.md and report declared packs that are not loaded."""

from __future__ import annotations

try:
    import json
    import os
    import subprocess
    import sys
    from pathlib import Path

    MARKETPLACE_SUFFIX = "@datazard-plugins"
    LIST_TIMEOUT_SECONDS = 5
    CONTEXT_CAP = 10_000

    def declared_packs(project):
        settings = json.loads((project / ".claude" / "settings.json").read_text(encoding="utf-8"))
        enabled = settings.get("enabledPlugins", {})
        return sorted(
            key
            for key, value in enabled.items()
            if value is True and key.endswith(MARKETPLACE_SUFFIX)
        )

    def real_list_plugins(project):
        try:
            done = subprocess.run(  # noqa: S603
                ["claude", "plugin", "list", "--json"],  # noqa: S607
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=LIST_TIMEOUT_SECONDS,
                check=True,
            )
            entries = json.loads(done.stdout)
            return entries if isinstance(entries, list) else None
        except Exception:
            return None

    def loaded_ids(entries, project):
        resolved = project.resolve()
        ids = set()
        for entry in entries:
            if not isinstance(entry, dict) or entry.get("enabled") is not True:
                continue
            if entry.get("scope") in ("user", "synced"):
                ids.add(entry.get("id"))
                continue
            path = entry.get("projectPath")
            if path and Path(path).resolve() == resolved:
                ids.add(entry.get("id"))
        return ids

    def missing_packs_line(env, list_plugins):
        project_dir = env.get("CLAUDE_PROJECT_DIR")
        if not project_dir:
            return ""
        project = Path(project_dir)
        try:
            declared = declared_packs(project)
        except Exception:
            return ""
        if not declared:
            return ""
        try:
            loaded = loaded_ids(list_plugins(project), project)
        except Exception:  # includes entries is None
            return ""
        missing = [pack for pack in declared if pack not in loaded]
        if not missing:
            return ""
        return (
            "Declared in .claude/settings.json but not loaded in this session: "
            + ", ".join(missing)
            + ". Run /plugin to install or enable them."
        )

    def main(stdin, env, list_plugins):  # noqa: ARG001 - the hook input is not needed
        try:
            root = Path(env["CLAUDE_PLUGIN_ROOT"])
            context = (root / "base.md").read_text(encoding="utf-8")
            line = missing_packs_line(env, list_plugins)
            if line:
                context = context.rstrip("\n") + "\n\n" + line
            context = context[:CONTEXT_CAP]
            return json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "SessionStart",
                        "additionalContext": context,
                    }
                }
            )
        except Exception:
            return ""

    if __name__ == "__main__":
        sys.stdout.write(main(sys.stdin.read(), os.environ, real_list_plugins))
except BaseException:  # a hook never fails a session
    raise SystemExit(0) from None
