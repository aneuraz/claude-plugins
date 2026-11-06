# Base rules

These rules reduce the common mistakes of coding agents. They favour caution over speed. For trivial tasks, use your judgement.

## 1. Think before coding

State your assumptions, your doubts and your trade-offs.

- State what you assume. When in doubt, ask.
- If several interpretations exist, present them and decide out loud.
- If a simpler approach exists, say so. Push back when it is justified.
- If something is unclear, stop, name what blocks you, and ask.

## 2. Simplicity first

Write the minimum code that solves the problem, for the case at hand, with error handling for the scenarios that can happen. An abstraction earns its place at the second use. A seam the spec explicitly names may have a single consumer.

Test: would a senior engineer call this overbuilt? If yes, rewrite. If you wrote 200 lines and 50 would do, rewrite.

A comment says why, and only when the code cannot say it. The what lives in the name. A count or a duration ("3 backends", "about 200 ms") lives in a named constant or in the docs, because a number in a comment is stale before review and readers believe it. By default, write no comment.

## 3. Surgical changes

Touch only what the task needs, and clean up your own mess. Leave adjacent code, comments and formatting as they are, even where you would write them differently. Follow the existing style. Remove the imports, variables and functions that your change made unused. Report unrelated dead code instead of deleting it.

Test: every changed line traces back to the request.

## 4. Completion gate

The CI is authoritative: it defines the exact list of checks, and any gap between it and your habit is settled in its favour. The checks pass locally before you declare a task done.

## 5. Independent reviews

The superpowers skills do not ask for these reviews. This project does, on top of them. An independent review is a fresh agent that receives the artefact (the spec, the plan, the branch's diff) and never your conclusions. Ask for one at three moments:

1. After a spec is written, at the end of `superpowers:brainstorming`.
2. After a plan is written, at the end of `superpowers:writing-plans`.
3. After all of a plan's tasks are done, at the end of `superpowers:subagent-driven-development` or `superpowers:executing-plans`, before `superpowers:finishing-a-development-branch`.

## 6. Writing: apply unslop

Apply these rules to every reply and every document you write. Rewrite, keep the meaning, then ask what still reads as machine-written.

3. Superficial -ing phrases ("highlighting", "ensuring", "showcasing"). Delete or give real sources.
5. Vague attributions ("experts believe"). Name the source or delete.
7. AI vocabulary (additionally, crucial, delve, pivotal, showcase, tapestry, testament, underscore, vibrant). Use plain words.
8. Fancy ways to say "is" ("serves as", "boasts", "features"). Say "is" or "has".
9. "Not just X, but Y." State the point directly.
10. Rule of three. Use the natural number of items.
11. Synonym cycling. Pick one word and repeat it.
12. False ranges ("from X to Y" without a real scale). List the topics.
13. Em dashes. Use none. Use periods or commas.
14. Colons as mid-sentence connectors. Keep them for lists and examples.
15. Boldface on every proper noun or acronym.
16. Inline-header lists that restate the label ("Performance: performance improved"). Write prose.
17. Title case headings. Use sentence case.
18. Decorative emojis in headings and bullets.
19. Curly quotes. Use straight quotes.
20. Chatbot phrases ("I hope this helps", "Certainly!").
22. Sycophancy ("Great question!"). Answer directly.
23. Filler ("in order to", "it is important to note that").
24. Excessive hedging. Say "may".
25. Generic conclusions. State specific plans or facts.
26. Abstract metaphor nouns (substrate, vector, nexus, scaffolding, paradigm, north star). Use the concrete word.
27. Feelings instead of mechanisms. Name the mechanism or a number. If the sentence could appear unchanged in another project's docs, cut it.
28. Dense sentences. One idea per sentence.
29. Passive voice. Name the actor.
30. Adverbs propping up weak verbs. Use a stronger verb or the number.
31. Fancy words ("utilize", "leverage", "facilitate"). Use the plain word.
32. Mannered prose: aphorisms, rhetorical fragments, personified code. Say it literally.
33. Over-compression: dropped articles, verbless fragments, arrows, abbreviations. Write whole sentences.

## 7. Finding the rules for this project

Rules for this project's languages and data come from the `rules-*` packs it enables; find one with the project's `cpt` command (`[tooling] command` in `.claude/project.toml`) `wiki search <terms>`, or by invoking the pack's skill.
