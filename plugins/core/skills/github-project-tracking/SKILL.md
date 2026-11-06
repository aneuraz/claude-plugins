---
name: github-project-tracking
description: Operate a repository's GitHub Project. Open a milestone's umbrella issue and its sub-issues, move cards, set fields, create labels, close a milestone. Invoke this skill BEFORE any `gh project` or `gh api graphql` command on a Project; the exact invocations cannot be guessed, and several measured traps make the obvious steps fail or lie.
---

# Tracking with the GitHub Project

The project's tracking rule page (`[tracking] rule_page` in `.claude/project.toml`, a path from the repository root) says **what** must be tracked and why. This skill says **how** to do it: the exact invocations, the identifiers to resolve, and the traps that have already cost time.

## Resolve the context first, never assume it

This skill hard-codes no repository, no Project number and no identifier; only the Project's title comes from `[tracking] project` in `.claude/project.toml`. **Resolve them from the current repository** before any other step. First read `[tracking] project` from `.claude/project.toml` and set `PROJECT_TITLE` to it; if the file or the key is absent, leave it empty: the script lists the Projects and you stop to **ask which one**.

```bash
OWNER_REPO=$(gh repo view --json nameWithOwner --jq .nameWithOwner)   # e.g. owner/repo
OWNER=${OWNER_REPO%/*}; REPO=${OWNER_REPO#*/}

# The Project's title is [tracking] project in .claude/project.toml; with no such key,
# ask which Project (see below) rather than guessing
PROJECT_TITLE=${PROJECT_TITLE:-}   # fill it from [tracking] project before running this
if [ -z "$PROJECT_TITLE" ]; then
  echo "No [tracking] project: pick one and ask the owner"
  gh project list --owner "$OWNER"
else
  PROJECT=$(gh project list --owner "$OWNER" --format json \
    --jq ".projects[] | select(.title==\"$PROJECT_TITLE\") | .number")
fi

echo "$OWNER_REPO — Project #$PROJECT"
```

If `$PROJECT` is empty, no Project has that title: set `PROJECT_TITLE` to the one the tracking rule page uses. If `[tracking] project` and the page name none, list the Projects (`gh project list --owner "$OWNER"`) and **ask which one** rather than guessing. Writing to the wrong Project does not show in the command output.

**One Project, several repositories.** The repositories the programme shares are `[repository] siblings` in `.claude/project.toml`. An issue of another repository is written `owner/repo#N`, in a `Closes` line too, and `gh issue` takes `--repo owner/repo` to reach it.

**Vocabulary:** a **milestone** is the grouping unit, an *umbrella* issue and its tasks as sub-issues. If the current repository says "plan" or "batch" rather than "milestone", use its word; the mechanics are the same. A milestone here is an umbrella issue with its sub-issues, not GitHub's native milestone object: never use `--milestone`.

The values you record (`PROJECT_ID`, `FIELD_ID`, `OPTION_ID`) are **specific to each Project**. Keep them in the repository's work log, not in this skill.

## Once, before the first milestone

These four points are an inventory to take on any new Project. Do not replay them on a live Project: point 2 is destructive.

### 1. Push the default branch, an **absolute prerequisite**

```bash
gh repo view --json defaultBranchRef \
  --jq 'if (.defaultBranchRef.name // "") == "" then "NONE" else .defaultBranchRef.name end'
```

⚠️ **Measured: on a repository with no branch, `gh` returns `{"defaultBranchRef":{"name":""}}`**, an empty
string, not `null`. A `--jq '.defaultBranchRef.name // "NONE"'` therefore catches **nothing** (`//` only
reacts to `null` and `false`) and prints an empty line that is too easily read as a success. Hence the
explicit test above. The check that does not lie:

```bash
git ls-remote --heads origin    # no output = no remote branch
```

If the answer is `NONE`, the remote repository has **no default branch**. Until that is fixed, `Closes #N` closes nothing (the keyword only acts when a PR is merged **into the default branch**), no PR can be opened, and the `Pull request linked to issue` workflow cannot fire, so no card moves on its own.

```bash
git push -u origin main
gh repo view --json defaultBranchRef --jq .defaultBranchRef.name   # must return the branch
```

Do not open a milestone issue until this command returns a branch name.

### 2. Complete the `Status` options

A new Project has only `Todo`, `In Progress`, `Done`. The repository's tracking cycle needs five. **Without `Ready` and `In Review`, the cycle cannot be represented**: `Ready` separates what is specified from what is not, and `In Review` holds the consistency review at the end of the milestone.

The target order: `Backlog` → `Ready` → `In Progress` → `In Review` → `Done`.

```bash
# read the CURRENT options with their ids; do not skip this step
gh project field-list "$PROJECT" --owner "$OWNER" --format json \
  --jq '.fields[] | select(.name=="Status") | {id, options: [.options[] | {name, id}]}'
```

⚠️ **`updateProjectV2Field` REPLACES the whole list.** Any option whose `id` is not passed again is deleted, and **the cards that held it end up with an empty `Status`**. Always read back afterwards.

⚠️⚠️ **MEASURED TRAP, THE COSTLIEST IN THIS SKILL: this mutation DISABLES the built-in workflows.**

Observed: seven workflows active before the call, **two after**. The five that carry the whole cycle,
`Auto-close issue`, `Item closed`, `Pull request linked to issue`, `Pull request merged` and
`Item added to project`, went to `enabled: false`. They referenced the options by `id`, and
GitHub **regenerates ALL the ids** on every `updateProjectV2Field`, including those passed back
unchanged. The references break and the workflows disable themselves silently.

**The GraphQL API exposes no mutation to re-enable them** (only `deleteProjectV2Workflow`
exists). The repair **must go through the web interface**: Project → ⋯ → Workflows
→ re-enable each one.

Practical consequences:

1. **Make this change ONCE, before the first milestone**, never on a live Project.
2. **Check the workflows immediately afterwards** (§3 below). Their disabling is
   completely silent, and a Project without them no longer moves any card on its own.
3. **Do not pass the existing `id`s back hoping to preserve them**: that does not preserve them.
   Just give the list you want, and know that the `OPTION_ID`s you had recorded are
   stale. Read them again.

### 3. Check the built-in workflows

Four workflows carry the cycle: `Auto-close issue` (card `Done` → issue closed), `Item closed` (the reverse), `Pull request linked to issue` (PR→issue link → card `In Progress`), `Pull request merged`. Never assume they are active after a change to the Project:

```bash
gh api graphql -f query="{ user(login:\"$OWNER\") { projectV2(number:$PROJECT) {
  workflows(first:20) { nodes { name enabled } } } } }" \
  --jq '.data.user.projectV2.workflows.nodes[] | "\(.enabled)\t\(.name)"'
```

For a Project owned by an organisation, replace `user(login:…)` with `organization(login:…)`.

Check whether `Auto-add sub-issues to project` is present and active. If it is, attached sub-issues reach the board on their own, without `item-add`. Its presence varies from one Project to another.

### 4. Resolve the identifiers once and for all

`item-edit` takes neither names nor numbers: four identifiers, all to be resolved first. They do not change, so keep them in the work log rather than resolving them again for every step.

```bash
gh project view "$PROJECT" --owner "$OWNER" --format json --jq '.id'        # PROJECT_ID
gh project field-list "$PROJECT" --owner "$OWNER" --format json \
  --jq '.fields[] | select(.name=="Status") | {id, options: [.options[] | {name, id}]}'   # FIELD_ID + OPTION_IDs
```

Record them in a table: `PROJECT_ID` (`PVT_…`), the `FIELD_ID` of the Status field (`PVTSSF_…`), and the short `id` of each of the five options.

The `FIELD_ID` survives an `updateProjectV2Field`; the `OPTION_ID`s do **not** (see the trap above).

### 5. Check where `Item added to project` puts the cards

Measured, right after the trap above: after re-enabling in the web interface, the
`Item added to project` workflow had been rewired to `In Progress`. The milestone's 22 issues therefore
**all arrived in `In Progress`**, a board showing twenty-two simultaneous work items
on the day it opened.

The API does not show a workflow's internal configuration (`workflows` returns only `name`
and `enabled`): it cannot be read, let alone fixed by a mutation. Two steps:

1. **In the web interface**, set `Item added to project` to `Ready`. It is the correct
   status for a task the plan covers but nobody has started.
2. **After any bulk creation of issues, read the statuses back** and fix them as needed:

```bash
# reset everything to Ready except the umbrella issue (the milestone's lowest number)
PROJECT_ID=<PVT_…>; FIELD_ID=<PVTSSF_…>; READY=<option-id>; UMBRELLA=<N>
gh project item-list "$PROJECT" --owner "$OWNER" --limit 200 --format json \
  --jq ".items[] | select(.content.number > $UMBRELLA) | .id" |
while read -r item; do
  gh project item-edit --id "$item" --project-id "$PROJECT_ID" \
    --field-id "$FIELD_ID" --single-select-option-id "$READY"
done
gh project item-list "$PROJECT" --owner "$OWNER" --limit 200 --format json \
  --jq '[.items[] | .status // "EMPTY"] | group_by(.) | map("\(length) × \(.[0])") | join("  |  ")'
```

The umbrella issue rightly stays in `In Progress`: opening a milestone means starting it.

## Opening a milestone: the umbrella issue and its sub-issues

**A milestone first opens its umbrella issue (`[plan] milestone N — <subject>`), then one issue per task, attached as a sub-issue.** The hierarchy gives the "12 of 21" progress; the label only groups.

Follow the writing language set by the repository's `CLAUDE.md` for issue titles and bodies. The body of a task issue does not copy the plan; it points to it ("Plan §Task A5").

`gh` does not expose sub-issues. Attaching goes through GraphQL, using **node IDs** (`I_kw…`), never issue numbers.

```bash
# node ID of an issue, from its number
gh issue list --state all --limit 100 --json number,id \
  --jq '.[] | select(.number==<N>) | .id'

gh api graphql -f query='
mutation($parent: ID!, $child: ID!) {
  addSubIssue(input: {issueId: $parent, subIssueId: $child}) {
    subIssue { number }
  }
}' -f parent=<NODE_ID_UMBRELLA> -f child=<NODE_ID_TASK>
```

**Read the counter back, not the mutation output.** Two measured facts point the same way:
four mutations had answered while the counter still showed `1 of 4` (delayed
propagation); elsewhere, a loop over 21 issues reported **7 successes and 14 `VALIDATION` errors**
while the counter showed `21 of 21`. The "errors" were attachments already
made, replayed by the loop. Both ways, the mutation output lies. Only the
counter is authoritative.

```bash
gh api graphql -f query="{ repository(owner: \"$OWNER\", name: \"$REPO\") {
  issue(number: <UMBRELLA>) { subIssuesSummary { total completed percentCompleted }
                             subIssues(first: 50) { nodes { number } } } } }"
```

**Attach only the milestone's tasks.** A `debt`, a `decision` or an amended `fact` born during the milestone keeps its label but stays **outside the hierarchy**. Attached, it would prevent closing the umbrella issue, whereas accepted debt is not work to do.

Show the `Sub-issues progress` column in the Project to read progress without opening the issues.

## Moving a card

```bash
# item ID, from the issue number
gh project item-list "$PROJECT" --owner "$OWNER" --limit 200 --format json \
  --jq '.items[] | select(.content.number==<N>) | .id'

gh project item-edit --id <ITEM_ID> --project-id <PROJECT_ID> \
  --field-id <FIELD_ID> --single-select-option-id <OPTION_ID>
```

### Read-back trap, twice over

`item-list --format json` puts field names **in lower case** (`status`) and **omits the key** when the field is empty. A `--jq '.Status'` therefore returns `null` on a correctly set field, which leads to the wrong conclusion that the write failed.

```bash
gh project item-list "$PROJECT" --owner "$OWNER" --limit 200 --format json \
  --jq '.items[] | "\(.content.number)\t\(.status // "EMPTY")"'
```

The default `--limit` is too low once the Project grows: a card missing from the output is not a missing card. A single milestone can hold about twenty tasks, so go up to 200.

### Do not hide the output of a write loop

With `>/dev/null 2>&1` on `item-edit`, a loop that fails on every pass prints exactly the same thing as a loop that succeeds. Confirmation comes from the **server read-back** above, never from the loop's `echo`s. This is the completion gate of `CLAUDE.md` applied to tooling.

## Branches

One branch per task, named after the repository's convention, typically `feat/<module>-<task>`
(e.g. `feat/store-a2-schema`) or `fix/<subject>`. A milestone carried out in one go can live on a
single branch `feat/milestone-1`. In that case each commit carries its `Closes #N` and the PR gathers them.

**A branch starts from the default branch, never from another unmerged branch.** Measured:
a second piece of work opened from a branch awaiting review took its twelve commits along, and
its PR would have mixed two unrelated subjects.

```bash
# fix if it has already happened; painless as long as nothing has been pushed
git rebase --onto main <last-commit-of-the-other-branch>
```

## The life cycle, step by step

| Moment | Task card | Milestone card (umbrella issue) | PR |
|---|---|---|---|
| The plan covers the task | `Ready` | `Ready` when the milestone opens | — |
| Implementation starts | — | `In Progress` | **opened as draft**, without `Closes` |
| A task starts | `In Progress` **through the added `Closes`** + assignment | — | `Closes #N` added |
| The code is delivered, review green, completion gate passed | **`Done`** | — | — |
| All tasks `Done`, consistency review closed | — | **`In Review`** | **`gh pr ready`** |
| The PR is merged | — | `Done` | — |

On the tooling side:

**When a task starts**, adding its `Closes #N` to the draft PR body is enough: the `Pull request linked to issue` workflow moves the card to `In Progress` on its own. Assign the issue at the same time.

```bash
gh pr view <PR> --json body --jq .body > /tmp/body.md
printf '\nCloses #%s\n' "<N>" >> /tmp/body.md
gh pr edit <PR> --body-file /tmp/body.md
gh issue edit <N> --add-assignee @me
```

**When a task's review is green**, move the card to `Done`. It is **the only mandatory manual step**: it triggers `Auto-close issue`, which closes the issue and increments the umbrella issue's counter. The `Closes #N` is only a safety net. Relying on it alone makes a fully delivered milestone show `0 of 21`.

**Follow the repository's completion gate before moving a card to `Done`.** Where the project keeps a fact-set, a task is `Done` only once its fact has moved to `@implemented` **in the same commit as the code**. A `Done` card whose fact stayed `@spec` is a traceability lie that no verification script catches: those scripts check the checks, not the statuses.

**An abandoned task** is closed as `not planned`, which takes it out of the counter; also remove its `Closes` from the PR body.

```bash
gh issue close <N> --reason "not planned"
```

**At merge**, close the umbrella issue and move its card to `Done`. First check that the counter reads `n/n`: an umbrella issue with a sub-issue still open cannot be closed.

```bash
gh issue close <UMBRELLA> \
  -c "Milestone delivered and merged in #<PR> (merge <sha>). n/n tasks complete."
```

## Checking that a PR will close its issues

The `Closes #N` keyword in the body does not prove that GitHub recorded the link. Read it back:

```bash
gh api graphql -f query="{ repository(owner:\"$OWNER\", name:\"$REPO\") {
  pullRequest(number:<PR>) { closingIssuesReferences(first:50) { nodes { number title } } } } }"
```

`Closes` closes an issue only **when a PR is merged**, or on a direct push to the default branch. Check which branch that is (`gh repo view --json defaultBranchRef`) before relying on it.

## The late PR trap

The `Pull request linked to issue` workflow pulls **every** issue a PR references into `In Progress`, `Done` ones included. A PR created at the end with its twenty `Closes` at once therefore sends the twenty cards of a delivered milestone back, and they have to be restored by hand.

This is why the draft PR opens early: `Closes` added task by task trigger the workflow while the cards are rightly in `In Progress`. **If you still end up creating a PR carrying several `Closes` at once, read the `Status` values back after creation and restore them.** Otherwise the board lies at the very moment someone comes to read it.

Measured: editing the description of an **existing** PR does not trigger this workflow; only creation does.

## Labels

Check what exists before creating anything. A new repository has only GitHub's default labels:

```bash
gh label list --limit 50
```

The five uses below carry the tracking. Adapt the names to those the repository's `CLAUDE.md` already uses:

| Label | Use |
|---|---|
| `milestone-1` / `milestone-2` … | task of the current milestone |
| `debt` | accepted deferral, recorded in the project's wiki through `updating-the-wiki` |
| `decision` | open trade-off |
| `security` | touches a guarantee of `SECURITY.md`. **Can be combined** |
| `fact` | changes the fact-set (statement, check or status) |

```bash
gh label create <name> -d "<description>"
```

The `fact` label only makes sense in a repository that keeps a fact-set: the fact-set is a versioned contract, and every change to it must be visible, including when it comes with a code fix. Leave it out elsewhere.
