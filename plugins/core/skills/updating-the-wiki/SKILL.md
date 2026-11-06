---
name: updating-the-wiki
description: "Wiki ingest: use when a milestone's documentation task starts, a debt is accepted, a decision or defect is closed, a rule changes, or a reading of the wiki finds a lesson it lacks."
---

# Updating the wiki

An ingest files what was learned into the project's wiki. The sources (specs, fact-sets, plans, reviews, the code) stay as they are, and the pages cite them. A page states one lesson, rule, decision, debt, defect, reference or how-to.

## Steps

0. **Read `.claude/project.toml`.** `[wiki] path` is the wiki's directory (`<wiki>` below); `[wiki] tooling` says whether `cpt` keeps the index (`"cpt"`) or you do (`"none"`); `[tooling] command` is how the project runs `cpt`. When the file is absent, say the project is not configured and stop; when `[wiki]` is absent, the project has no wiki: say so and stop.
1. **Find the touched pages through `<wiki>/index.md`.** Done when you have listed every page the new knowledge extends, contradicts or makes stale, and the hub each one belongs under.
2. **Extend an existing page when the lesson is the same.** Add to its text or rewrite it. A page's slug, its file name, is permanent; its title is edited in place.
3. **Write a new page when it is not**, at `<wiki>/<type directory>/<slug>.md`, with this front matter, and link it from its hub or a neighbouring page:

   ```yaml
   ---
   title: <the lesson, stated as a sentence>
   type: lesson        # hub, lesson, rule, defect, debt, decision, reference or howto
   sources:
     - path: <a file in this repository the page comes from>
       commit: <the output of `git merge-base HEAD origin/main`>
   status: current
   issues: [<N>]       # debt, defect, decision: their issue numbers
   ---
   ```

   Issue references in the text take the form `[repository] issue_reference` gives, with `{n}` the number (it names `[repository] issue_repository`). When `issue_reference` is absent, write `#N` for this repository and `owner/repo#N` for another. A page merged into another keeps its file, with `status: superseded` and `superseded_by: <wiki>/<type directory>/<slug>.md`, the path from the repository root of the page that holds it now.

   A source whose commit is not in this repository's history (`git cat-file -e <commit>` fails) is a commit of a sibling in `[repository] siblings`: its file is read at the URL `[repository] foreign_commit_url` gives, with `{repo}`, `{commit}` and `{path}` filled in, whichever sibling holds it. When the key is absent, name the commit's repository and path and say the URL is not configured.
4. **Append one entry to `<wiki>/log.md`**, after the last one: a heading `## [YYYY-MM-DD] ingest | <what was ingested>`, a blank line, then one list item per page touched, a link whose text is the page's title, in the form the entries above it use.
5. **Refresh and check the index.** First check the keys: when `[wiki] tooling` is absent, or is `"cpt"` while `[tooling] command` is absent, say which key is missing, tell the owner, and stop before this step; do not guess.
   - With `tooling = "cpt"`: run the project's `cpt` command (`[tooling] command`) with `wiki index`, then with `wiki check`. Each fault names the file, the line and the rule; `wiki check --help` says what each rule refuses. Fix and rerun.
   - With `tooling = "none"`: update `<wiki>/index.md` by hand. Add each new page under its type's heading, in title order, a link whose text is the page's title; remove nothing, a superseded page stays listed. Then check that every relative link you wrote resolves to a file. Done when each new page appears in the index and has an inbound link from another page or is a hub.

## Done when

With `cpt`: `wiki check` exits 0 and the log entry names every page the ingest touched. Without: the index lists every page the ingest created, every link resolves, and the log entry names every page the ingest touched.
