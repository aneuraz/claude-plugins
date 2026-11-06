---
name: spec-to-facts
description: Extracts testable contracts and executable assertions ("facts") from design docs and specs, producing a fact-set with a @draft → @spec → @implemented → @superseded lifecycle that feeds TDD plans and CI gates. Designed to slot into the superpowers workflow - use it right after superpowers:brainstorming has saved and committed an approved design doc, before or at the start of superpowers:writing-plans, so the plan's failing tests come from facts instead of ad-hoc invention. Also use standalone whenever the user writes, reviews, or critiques a spec, PRD, or requirements doc; asks to extract invariants, testable acceptance criteria, or API contracts; mentions spec drift or wants to "harden" / "make testable" a spec; or brings up facts-first, contract testing, property-based testing, or Design by Contract. Trigger even if the user simply asks to "improve this spec."
---

# Spec → Facts: testable contracts from design docs

Guiding principle: **a prose spec is a prediction about whoever reads it; a fact is an executable assertion verified by an exit code.** Prose gets reinterpreted at every reading (by humans or LLMs); a test passes or fails, with no interpretation. This skill does not replace the design doc: the design doc carries the "why" and stays authoritative for humans. The fact-set carries the machine-verifiable "what".

**Announce at start:** "I'm using the spec-to-facts skill to extract testable contracts from the design."

**Tooling.** Commands below are `facts …` subcommands of the project's `cpt` command (`[tooling] command` in `.claude/project.toml`). If the file or the key is missing, say the tooling is "not configured" and fall back to an inline equivalent; do not guess a command.

## Where this fits in the superpowers pipeline

```
brainstorming ──> design doc approved & committed
                      │
                      ▼
              spec-to-facts          <── YOU ARE HERE
                      │  writes <topic>-facts.md + back-references in the design doc
                      ▼
              writing-plans          each task's failing test = a fact's test
                      ▼
  subagent-driven-development        green check ⇒ promote @spec → @implemented
  (or executing-plans)               final gate: CI reads the test reports
```

Do not interrupt brainstorming itself: it forbids invoking other skills mid-flow. Run after the design doc exists. If writing-plans has already started without a fact-set, pause, extract facts from the design doc first, then resume planning against them.

## Step 1 — Extract invariants from the design doc

Input: the approved design doc (default location `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`). Read it sentence by sentence and extract every assertion a machine can verify. Signals: "must", "always", "never", "at most", "returns", "rejects", "before/after", error codes, formats, bounds, uniqueness, idempotence, latency budgets.

Classify each invariant at one of **three granularity levels**:

1. **Test (example)**: one precise input/output pair. *"An expired JWT on `/auth/refresh` returns 401."*
2. **Property (universal quantification)**: a predicate over a whole input domain, a property-based-testing candidate. *"For every valid FHIR Bundle as input, the pipeline output is a valid Bundle against the R4 profile."*
3. **Contract (pre/post/invariant)**: Design by Contract at the level of a module, API, or data schema. *"Precondition: active patient consent; postcondition: no identifying data leaves the certified perimeter; invariant: enrichment never reduces the resource count."*

Also flag **implicit invariants**: rules stated only in prose with no assertion anywhere in code. Prioritize high-risk surfaces: auth, payment, health/personal data, data federation.

What does NOT become a fact: intent, context, trade-offs, architecture rationale. That prose is the design doc's job and is irreplaceable. If an invariant is not testable as stated (vague: "the interface must be intuitive"), do not invent a test: record it as `@draft` with a `blocker:` note and ask the user.

## Step 2 — Write the fact-set

Save to `docs/superpowers/specs/YYYY-MM-DD-<topic>-facts.md`, sibling of the design doc, and commit it with the same conventions. The file is markdown **that is also valid YAML** (one entry per fact), human-readable and script-parsable:

```yaml
- id: AUTH-001
  status: "@spec"          # @draft | @spec | @implemented | @superseded
  level: test              # test | property | contract
  statement: "An expired JWT on POST /auth/refresh returns 401 with code=TOKEN_EXPIRED"
  check: "<runner command naming the test, e.g. tests/contracts/test_auth.py::test_expired_jwt_returns_401>"
  source: "2026-08-31-auth-refresh-design.md §Token lifecycle"
  owner: backend
  requires: []             # optional: resource names the check needs (e.g. a database); see facts --exclude-requires
  superseded_by: AUTH-007  # @superseded only: the id, or a list of ids, of the facts binding in its place
```

Rules:
- `check` is **a command that runs this fact's test alone; exit code 0 is the truth condition**, and it names its test. Never a subjective criterion. Use the same command format as writing-plans verification steps (`Run:` / `Expected:`) so plans can embed it verbatim.
- `check` takes **one of the project's fixed forms** (the runner, its environment flags, the selector syntax, verbosity), listed in `[facts] check_forms` of `.claude/project.toml`; the gate refuses a pytest check in none of them: a flag outside the form (a test filter, a plugin switch, a shell operator) would make the command differ from what the reports prove. When `[facts] check_forms` is absent, say the forms are not configured and that the gate audits none. The selector syntax is the language's: for pytest see `rules-python:pytest-check-selector`.
- Lifecycle: `@draft` (invariant identified, no test yet) → `@spec` (test written, expected to fail until implemented; that is TDD) → `@implemented` (check green in CI) → `@superseded` (the invariant was replaced by a later design; the fact stays for history and the gate skips it). A superseded fact names its successors in `superseded_by`, an id or a list of ids; each must exist and be `@implemented`, or the gate fails. A dropped invariant has no successor: delete its fact from the fact-set and its id from the design doc.
- `source` covers only the fact→spec direction; the spec→fact direction is Step 2b. One without the other is half a contract.
- One fact = one assertion. No "and". Split.
- For deliberately non-deterministic behavior (LLM/NLP output), write properties over **structural or bound invariants** (valid output schema, floor score on a gold set, p95 latency), never exact text equality.

After Step 2b, present the fact-set to the user for review before handing off to writing-plans, same as brainstorming does with the design doc.

## Step 2b — Back-reference the facts in the design doc (REQUIRED)

Step 2 is **not complete** until the design doc points back at the fact-set. Three artifacts, all mandatory:

1. **Header pointer**: one line in the design doc header linking the facts file, the lifecycle (`@draft → @spec → @implemented`), and the sync discipline: *a new invariant creates its fact first; an orphan fact (no source section) is a spec bug.*
2. **A `*Facts: ID, ID…*` line closing every normative section**, listing the facts that lock it. Where a section deliberately stays prose (usage metrics, legal gates, deferred phases), say so on that same line: silence is indistinguishable from omission.
3. **Zero-orphan check**: run `facts --orphans` through the project's `cpt` command. It asserts every fact `id` appears in its sibling design doc (ranges like "SPL-001 to SPL-008" are expanded first) and exits non-zero on any orphan. Commit spec and facts in the same commit.

Do not present for review or hand off to writing-plans with any of the three missing: a fact-set the spec never acknowledges drifts from it by the second edit.

## Step 3 — Feed writing-plans

When writing-plans runs with a fact-set present:

- **Every fact `@draft`/`@spec` must be covered by a task.** Add "fact coverage" to the plan's self-review checklist, alongside spec coverage: for each fact, point to the task that implements its test. List gaps.
- **Task Step 1 ("Write the failing test") comes from the fact.** The test code in the plan is the fact's test; the task's `Run:` command is the fact's `check`. Reference the fact ID in the task header: `### Task 3: Refresh-token expiry [AUTH-001]`.
- New behavior discovered during planning ⇒ add a fact first (`@draft`), then the task. Facts and plan stay in sync.

## Step 4 — Execution and CI gate

During subagent-driven-development or executing-plans:

- When a task's verification passes (`check` exits 0), **promote the fact** `@spec` → `@implemented` in the facts file, in the same commit as the implementation.
- Before branch finishing, run `facts --orphans` (Step 2b's zero-orphan condition stays enforced for life, not just at extraction), then the `check` of every fact the branch adds or changes, verbatim. A red fact is a blocker: stop and ask, per executing-plans discipline.
- The full gate is CI's job: each test job writes a report of its tests' outcomes, and a gate job runs `facts --reports <directory>` over them. Offer to add the two parts to CI so facts keep guarding the codebase after the branch merges. Do not run every `check` locally or in CI: that re-runs the suites to re-prove what they already proved, and a skipped test still exits 0. The gate contract is in `references/gate.md`.

## Step 5 — Close the milestone

- **A consistency review runs on the whole branch before the PR leaves draft.** A task review compares a diff with a brief; it cannot see what only shows at the scale of the whole, and a defect can survive ten successive task reviews if each task matches its brief while the overall contract is broken. The review pays off precisely because it is cross-cutting: it looks for what a siloed review lets through. When every task is delivered and reviewed, review the branch as one piece for: an invariant set in one module and not honoured in another; a spec promise that does not hold end to end (take one and follow it to the output); a test that bears a fact's name but checks less than its statement; dead or duplicated code left by successive fixes; documentation that no longer matches the code; deferred debts (which must close before merge, which can wait). Fix the findings on the branch.
- **Every milestone ends with a documentation task.** It is not optional and is not postponed to the next milestone. What gets lost is the reasoning (why this mechanism rather than another, which defect it closes, why the obvious solution was wrong): during development it lives in reviews and conversations, all ephemeral. Unwritten, it disappears, and the next contributor will reopen a defect already closed. The task covers three things:
  1. **The wiki**, through `core:updating-the-wiki`: the structural decisions, the closed defects, and the lesson from each, one page per lesson. A defect found in review that took several fixes gets its page, with what made it hard. The wiki is what you read, through `core:reading-the-wiki`, to understand why the code is the way it is.
  2. **Updating what exists**, spec, fact-set, front page, wiki pages: what a milestone made false is corrected in the same milestone. Stale documentation does more harm than missing documentation, because people trust it.
  3. **Accepted debts**: what was deliberately deferred, with the reasoning that makes the deferral acceptable, **and what would make it unacceptable**. Without that last clause, the debt is a wish.
- **Check what you write.** A documented command gets run; a figure comes from a measurement or is marked as an estimate. A document that lies about a command is worse than no document.
- **What git does not track does not exist.** Review reports and progress logs are ephemeral: copy what must survive into a versioned document.

## Standalone mode (no superpowers pipeline)

When invoked on an arbitrary spec/PRD outside the brainstorming → plans flow, add a **triage step first**: for each section, ask "is this artifact read by a human outside the team (auditor, regulator, B2B partner, new hire)?" Yes → it stays prose (compliance, onboarding, the "why"); no, and it describes verifiable system behavior → conversion target. Present the triage as two lists before converting anything, then proceed with Steps 1–2. Deliverables by request type:

| User request | Deliverable |
|---|---|
| "Improve / harden this spec" | Triage + annotated spec + `@draft` fact-set |
| "Make this spec testable" | Full fact-set + `@spec` tests + the report plugin and the gate job |
| "Facts-first audit of the repo" | Spec inventory (kept / dead / implicit invariants) + top 10 at-risk invariants |
| "Set up the CI gate" | Report writer in each test job + `facts --reports` job + merge rule |

## References

- `references/gate.md`: the report format, the gate's three modes and flags, the CI wiring in outline. Read it at Step 4 or when setting up the gate.
- `references/test-patterns.md`: what to write per fact level, where each language's templates live, the Pact template (cross-language), and a prose-to-fact conversion cheat sheet. Read it when generating tests (Step 3).
