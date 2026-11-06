---
name: reading-the-wiki
description: "Wiki lookup: use before answering why something is built the way it is, which rule governs it, or how to run a procedure in this repository, and before concluding that no rule applies."
---

# Reading the wiki

The project's wiki is its memory: one page per lesson, rule, decision, debt, defect, reference or how-to, each citing the sources it came from. The code shows what is built; the wiki holds why, and which fixes were already tried. The enabled rule packs hold the rules that travel between projects.

## Steps

0. **Read `.claude/project.toml`.** `[wiki] path` is the wiki's directory; `[tooling] command` is how the project runs `cpt`. When the file is absent, say the project is not configured; when `[wiki]` is absent, say the project has no wiki. In both cases skip steps 1 and 2 and go to step 3 (the packs only).
1. **Read `<[wiki] path>/index.md`.** It lists every current page by type, then the glossary, the decisions and the raw sources (specs, fact-sets, plans, research). Done when you have picked every page whose title bears on the question.
2. **Open those pages.** A hub's text frames a milestone or a family of rules and lists its pages. **Follow their links until the question is covered.** Done when each part of the question rests on a page you have read, or you have followed the index and the hubs around it and no page holds it.
3. **Search.** Run the project's `cpt` command (`[tooling] command` in `.claude/project.toml`) with `wiki search <terms>`: it covers the project's wiki and the enabled packs, lists every page or rule matching any of the terms, and ranks first those matching the most. Give several words, synonyms included: a rule's wording may not be the question's. Open what it returns; `wiki show <citation>` prints a cited page or rule. When the file or `[tooling] command` is absent, say the search is not configured.
4. **Read the packs' rule titles.** Invoke each enabled `rules-*` pack skill (its SKILL.md lists its rules' titles), even when the search ran, and open the rules whose title bears on the question: a title can name the question in words the search did not try.
5. **Answer, citing the pages.** Each claim carries a relative link to its page, the page's title as the link text; in a code comment, `wiki:<directory>/<slug>`. A pack rule is cited as `<pack>:<slug>` (`rules-security:parameterised-sql`), in prose and in code alike: its file lives in the plugin, not in the project.

Answer "no rule covers this" only after the index, the search (where configured) and the enabled packs' rule titles all came back empty.

## A gap

When no page covers part of the question, say which part. Read the raw sources the index lists, or the code, and answer from them, marking those claims as absent from the wiki. Then, when the project has a wiki, offer to file the answer back as a page through `updating-the-wiki`, and run it once the owner agrees.

## Done when

Every claim in the answer cites a page or a pack rule, or is marked as absent from the wiki.
