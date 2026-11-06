---
name: qa
description: Run a black-box QA pass of the current branch on the project's QA stack, through its test surfaces, and get a report. Reads every command from [qa] in .claude/project.toml.
disable-model-invocation: true
argument-hint: "[spec path] [--keep]"
---

Run a QA pass of the branch checked out here. Arguments: $ARGUMENTS (an optional spec path, and `--keep` to leave the stack running for a replay by hand).

Every command below is read from `[qa]` in `.claude/project.toml`; the keys are `up`, `down`, `status`, `guard`, `up_keep`, `down_respect_keep`, `variables`, `surfaces`, `work_dir`, `errors_dir`, `tooling_paths`. When the file, the `[qa]` section, or any of `up`, `down`, `status`, `work_dir` is absent, say that QA is not configured for this project, name what is missing, and stop. Never guess a command. A project that runs QA also holds a `qa` agent in `.claude/agents/qa.md`; when it is absent, say so and stop.

1. **Check the variables.** When `[qa] variables` is set, check each name for presence in the environment without printing a value (for instance with the project's runner and a one-line script that prints only the names of the missing ones). When names are missing, ask the owner, in one question, for the value of each, pointing at the project's documentation for what it is. Done when you hold a value for each, from the environment or from the owner.

2. **Check the tooling.** When `[qa] tooling_paths` is set, run `git fetch origin main`. If it fails (offline, say), tell the owner so and go on against the last fetched `origin/main`; if `git rev-parse --verify origin/main` also fails, there is nothing to compare with: stop and ask the owner. Then run `git diff --stat origin/main -- <tooling_paths>`, which shows what this branch changes in the QA tooling, committed or not, and `git status --porcelain -- <tooling_paths>`, which also shows a file not yet tracked (the paths written out, separated by spaces). When either prints anything, show the owner both outputs as printed and ask, in one question, whether to go on: this branch's own guard and stack would confine the subagent and hold their key. This check is only as sound as this file, which is the branch's too: it guards against a careless change, not a hostile branch. Done when both print nothing or the owner has said to go on; otherwise stop here.

3. **Start the stack.** From the worktree's root, run `[qa] up`, or `[qa] up_keep` when the arguments hold `--keep` and both `up_keep` and `down_respect_keep` are set (when either is missing, say keeping is not configured here and run the normal `up`, and the normal `down` in step 6). Prefix it with `NAME=value` for each variable the owner gave in step 1, the value single-quoted as `shlex.join` would write it so a path with a space stays one word. Run it with Bash in the background and wait for its completion notification; a first build may take several minutes. Relay to the owner, as printed, any warning. Done when it has exited: on a non-zero exit, show the owner its message as it is, run step 6, and stop.

4. **Watch, then delegate.**
   - When `[qa] errors_dir` is set, arm a Monitor, `timeout_ms` 1800000, described "QA stack errors", on a command that prints each new `*.txt` file of that directory once, with its name and its first 400 characters, and polls every two seconds. When it is not set, arm no Monitor.
   - Read `${CLAUDE_SKILL_DIR}/METHOD.md` in this session, in full. Build the delegation prompt for the project's `qa` agent from: the full text of `METHOD.md`; the `[qa] surfaces` table rendered as name, command, description; the `core` version, which is the version segment of `${CLAUDE_PLUGIN_ROOT}` (the directory name just above `core`'s root in the plugin cache path, or its marketplace commit when the path has none); the work directory, which is `[qa] work_dir`; the base ref (`main`); and the spec to test, which is the path from the arguments or "the specs the diff touches" when none was given. The agent receives the method in the prompt and so needs no read outside the worktree.
   - Delegate to the `qa` subagent, in the background, with that prompt. Relay each Monitor event to the owner as it arrives, in one line. When the Monitor expires and the subagent is still running, arm it again. Done when the subagent's completion notification has arrived; then stop the Monitor.

5. **Keep the report.** The subagent's final message is the report. When the project's `down` writes it to a file, that file is the report; otherwise write the message to `report.md` in the work directory. Done when the report is on disk, or its absence is known.

6. **Tear down.** Whatever happened before, run `[qa] down_respect_keep` when the run was started with `up_keep`, else `[qa] down`. It is safe after the subagent's own teardown. Done when it has exited; on a non-zero exit, show the owner its message.

7. **Hand over.** Give the owner the path of the report and its **Summary** line, or say that the subagent ended without a report when it is missing. With `--keep`, add the command line that stops the stack: `[qa] down_respect_keep` for a kept run (started with `up_keep`), `[qa] down` otherwise. Done when the owner has the path or the absence.

## Notes

- **The agent stays in the project.** `.claude/agents/qa.md` is the project's: its own tools, its PreToolUse guard (`[qa] guard`), its MCP servers, its stop hook. This skill supplies the method and the orchestration; it neither ships nor overrides the agent.
- **The guard stays in the project too.** The command confinement (`scripts/qa/guard.py` in the first project that has one) is not part of the package in this release. Whether it joins the package is reconsidered when a second project's guard is ported.
- The method is `METHOD.md`, next to this file. A project that changes how the agent works changes its own agent file, not the method.
