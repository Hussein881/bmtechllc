---
title: Implementing a Project with Claude Code
description: Implementing a Project with Claude Code
owner: ah
updated: '2026-08-09'
tags: []
status: draft
visibility: internal
reviewCycleMonths: 6
order: 50
related: []
---

# Implementing a Project with Claude Code — A Working Playbook

A practical guide to setting up and running a project so that Claude Code produces
verifiable, reviewable work instead of plausible-looking output.

---

## 0. The one constraint everything else follows from

Almost every practice in this guide exists to manage a single thing: the context window
fills up fast, and model performance degrades as it fills. The context holds your entire
conversation — every message, every file read, every command output. A single debugging
session can consume tens of thousands of tokens, and as the window fills, Claude starts
losing earlier instructions and making more mistakes.

Two consequences shape the whole setup:

1. **Anything loaded into every session is expensive.** That's why CLAUDE.md should be
   short and skills should hold the long material.
2. **Anything that reads a lot of files should happen somewhere other than your main
   session.** That's why subagents exist.

The second constraint is behavioral rather than mechanical: **Claude stops when the work
looks done.** Without a check it can run, "looks done" is the only signal available, and
you become the verification loop. Every practice under §4 and §5 exists to remove you from
that loop.

---

## 1. The file layout

```
your-project/
├── README.md                      # for humans (and Claude, via @import)
├── SPEC.md                        # what we're building, written before code
├── PLAN.md                        # current phase's implementation plan
├── CLAUDE.md                      # persistent instructions, committed
├── CLAUDE.local.md                # your personal overrides, gitignored
├── .claude/
│   ├── settings.json              # permissions, hooks — committed
│   ├── settings.local.json        # machine-local overrides — gitignored
│   ├── rules/
│   │   ├── testing.md             # path-scoped conventions
│   │   └── api-design.md
│   ├── skills/
│   │   ├── phase-gate/SKILL.md    # procedures
│   │   └── run-<app>/SKILL.md
│   └── agents/
│       ├── reviewer.md            # subagent definitions
│       └── security-reviewer.md
└── tests/
    └── fixtures/                  # golden outputs Claude can diff against
```

Plus, outside the repo:

```
~/.claude/CLAUDE.md                              # your prefs, all projects
~/.claude/skills/                                # your personal skills
~/.claude/projects/<project>/memory/MEMORY.md    # auto memory (Claude writes this)
```

### What goes where — the decision table

| Kind of content | Home | Why |
|---|---|---|
| Facts true in **every** session (build commands, layout, gotchas) | `CLAUDE.md` | Loaded every session |
| Convention that applies to **one subtree only** | `.claude/rules/*.md` with `paths:` frontmatter | Loads only when Claude touches matching files |
| A **procedure** with steps | `.claude/skills/<name>/SKILL.md` | Body loads only when invoked |
| Long **reference material** | supporting files inside the skill directory | Loaded on demand, near-zero cost until read |
| Something **Claude figured out** and should keep | auto memory | Claude writes it; you audit with `/memory` |
| A rule that **must not be violated** | a hook | CLAUDE.md is advisory; hooks are deterministic |
| A delegation boundary | `.claude/agents/*.md` | Isolated context, restricted tools |

The last row of that table is the one people get wrong most often. CLAUDE.md instructions
are context, not enforced configuration — Claude reads them and tries to follow them, but
there's no guarantee of strict compliance. If a rule must hold every time with zero
exceptions, it's a hook.

---

## 2. Day 0 setup, in order

### 2.1 README.md first

Write it before CLAUDE.md, because CLAUDE.md can just point at it:

```markdown
See @README.md for project overview and @package.json for available commands.
```

Imported files are expanded into context at launch, so this isn't free — but it beats
maintaining the same description in two places and letting them drift.

### 2.2 Generate CLAUDE.md with `/init`, then cut it in half

`/init` analyzes your codebase to detect build systems, test frameworks, and code patterns.
It gives you a foundation. It also gives you a lot of material Claude could have derived by
reading the code, which is pure context tax.

The editing test for every line: **"Would removing this cause Claude to make mistakes?"**
If not, cut it.

| Include | Exclude |
|---|---|
| Bash commands Claude can't guess | Anything Claude can figure out by reading code |
| Style rules that differ from language defaults | Standard conventions Claude already knows |
| Test instructions and preferred runners | Detailed API docs (link instead) |
| Repo etiquette (branch naming, PR conventions) | Information that changes frequently |
| Architectural decisions specific to this project | File-by-file descriptions of the codebase |
| Environment quirks (required env vars) | "Write clean code" — self-evident practices |
| Non-obvious gotchas | Long explanations or tutorials |

Target under 200 lines. Longer files consume more context and reduce adherence — and the
failure mode is nasty because it's silent: **if Claude keeps ignoring a rule you wrote,
the file is probably too long and the rule is getting lost in the noise.**

Verify it actually loaded with `/context` — check the list under **Memory files**.

Two levers when adherence still lags:

- Emphasis (`IMPORTANT`, `YOU MUST`) measurably improves adherence.
- If Claude already does the thing correctly without the instruction, delete the line — or
  convert it to a hook if it truly must hold.

Treat CLAUDE.md like code: review it when things go wrong, prune regularly, and test
changes by watching whether behavior actually shifts. `/doctor` will also propose trims,
cutting content derivable from the codebase while keeping pitfalls and rationale.

### 2.3 Permissions, before you get click-fatigue

Default behavior asks approval for anything that modifies your system. That's safe and
tedious — and after the tenth approval you're not reviewing, you're clicking through.
Three ways to reduce the noise:

- **Allowlists** via `/permissions` for commands you approve constantly (`npm run lint`,
  `git commit`)
- **Auto mode** — a separate classifier reviews commands and blocks scope escalation,
  unknown infrastructure, and hostile-content-driven actions
- **Sandboxing** via `/sandbox` for OS-level filesystem and network isolation

Set at least one deny rule for something that must never happen. Deny rules are cheap
insurance.

### 2.4 Skills for procedures, not facts

Create a skill the moment you notice either signal:

- you've pasted the same instructions, checklist, or multi-step procedure into chat twice
- a section of CLAUDE.md has grown into a *procedure* rather than a *fact*

Minimum shape at `.claude/skills/<name>/SKILL.md`:

```yaml
---
description: >
  Runs the phase completion gate. Use when the user says a phase is done,
  asks to verify a phase, or asks whether scope was met.
disable-model-invocation: true
---

## Instructions
1. Read PLAN.md and extract the phase's acceptance criteria...
```

Field notes:

- `description` is the field that determines whether the skill ever fires. Write it with
  the phrases you'd actually type. Put the key use case first — the listing is truncated
  at 1,536 characters.
- `disable-model-invocation: true` for anything with side effects. You don't want Claude
  deciding to deploy because the code looks ready.
- `user-invocable: false` for background knowledge that isn't a meaningful command.
- `paths:` to limit activation to a subtree.
- Keep `SKILL.md` under 500 lines; push detail into sibling files that load on demand.
- Once invoked, the rendered content stays in context for the rest of the session, so
  every line is a *recurring* cost. Write standing instructions, not one-time steps.

### 2.5 Subagents for anything that reads a lot

Define them in `.claude/agents/`:

```markdown
---
name: plan-reviewer
description: Checks a diff against PLAN.md and reports gaps
tools: Read, Grep, Glob, Bash
model: opus
---
You are reviewing an implementation against a written plan.
Report only gaps that affect correctness or stated requirements.
Do not report style preferences.
```

Subagents run in their own context with their own allowed tools, so exploration doesn't
consume your main window.

### 2.6 Let Claude write your hooks

Hooks run scripts at fixed lifecycle points and are deterministic. You don't have to hand-
author the JSON — ask directly: *"Write a hook that runs the linter after every file
edit"*, or *"Write a hook that blocks writes to the migrations folder."* Browse what's
configured with `/hooks`.

---

## 3. Before any code: the spec phase

The highest-leverage habit in this entire document. Start a session with a minimal prompt
and let Claude interview you:

```
I want to build [brief description]. Interview me in detail using the
AskUserQuestion tool.

Ask about technical implementation, UI/UX, edge cases, concerns, and tradeoffs.
Don't ask obvious questions, dig into the hard parts I might not have considered.

Keep interviewing until we've covered everything, then write a complete spec
to SPEC.md.
```

Then **start a fresh session to execute it.** The new session has clean context focused
entirely on implementation, and you have a written artifact to reference and diff against
later.

A good spec is self-contained: it names the files and interfaces involved, states what is
**out of scope**, and ends with an end-to-end verification step that proves the feature
works. Time spent making the spec precise pays off more than time spent watching the
implementation.

The out-of-scope section is what makes phase gates enforceable later. If "deferred" isn't
written down before implementation, "we adopted it early" and "we forgot it" are
indistinguishable at review time.

---

## 4. The per-task loop

### Explore → Plan → Implement → Verify → Commit

**Explore.** Enter plan mode (`Shift+Tab` until the status bar shows `⏸ plan mode on`, or
launch with `claude --permission-mode plan`). Claude reads and answers without changing
anything.

```
read src/pipeline/ and understand how stage-1 classification decides
to escalate. also look at how we thread confidence thresholds through config.
```

**Plan.** Ask for a detailed implementation plan. Press `Ctrl+G` to open it in your editor
and edit it directly before approving. Save it as `PLAN.md` — you'll review the diff
against it later.

**Implement.** Exit plan mode and let Claude build, with the verification step in the same
prompt.

**Verify.** See §5.

**Commit.** Ask for a descriptive commit and a PR.

### When to skip planning

Plan mode adds overhead. If you could describe the diff in one sentence — a typo, a log
line, a rename — skip it. Planning earns its cost when you're uncertain about the
approach, when the change spans multiple files, or when you're unfamiliar with the code.

### Prompt precision

| Weak | Strong |
|---|---|
| "add tests for foo.py" | "write a test for foo.py covering the case where the session has expired. avoid mocks." |
| "fix the login bug" | "users report login fails after session timeout. check `src/auth/`, especially token refresh. write a failing test that reproduces it, then fix it" |
| "add a widget" | "look at how existing widgets are implemented; `HotDogWidget.php` is a good example. follow that pattern. don't add libraries not already in the codebase." |
| "the build is failing" | "the build fails with: [paste error]. fix it and verify the build succeeds. address the root cause, don't suppress the error." |

Vague prompts have a legitimate use — *"what would you improve in this file?"* surfaces
things you wouldn't think to ask. Use them when you're exploring and can afford to
course-correct, not when you're implementing.

---

## 5. Verification: the ladder

This is the difference between a session you watch and one you walk away from. The check
is anything returning a signal Claude can read: a test suite, a build exit code, a linter,
a script that diffs output against a fixture, a screenshot compared to a design.

Four rungs, each trading setup effort for attention:

| Rung | Mechanism | Good for |
|---|---|---|
| 1 | Ask Claude to run the check and iterate, in the same prompt | Any task, today, zero setup |
| 2 | A `/goal` condition — a separate evaluator re-checks after every turn | Multi-turn work in one session |
| 3 | A **Stop hook** running your check as a script, blocking the turn from ending until it passes | Unattended runs |
| 4 | An **adversarial subagent** — a fresh model tries to refute the result | Anything you'll ship |

Rung 4 is the one that matters most for your review discipline, and the reason is
structural: *the agent doing the work isn't the one grading it.* A reviewer running in a
fresh subagent context sees only the diff and the criteria you give it, not the reasoning
that produced the change.

```
Use a subagent to review the stage-2 escalation diff against PLAN.md.
Check that every requirement is implemented, the listed edge cases have tests,
and nothing outside the task's scope changed. Report gaps, not style preferences.
```

The bundled `/code-review` skill does the correctness version of this automatically on
your current diff.

**Two rules that prevent the most common failure:**

1. **Demand evidence, not assertion.** Have Claude show the test output, the command it
   ran and what it returned, or the screenshot. Reviewing evidence is faster than
   re-running the verification yourself, and it works for sessions you weren't watching.
   "All tests pass" is a claim; a paste of the runner output is evidence.

2. **Discount reviewer findings appropriately.** A reviewer prompted to find gaps will
   usually report some even when the work is sound, because that's what it was asked to
   do. Chasing every finding leads to over-engineering — extra abstraction layers,
   defensive code, tests for cases that can't happen. Tell the reviewer to flag only gaps
   affecting correctness or stated requirements, and treat the rest as optional.

### Test strategy that works with an agent

- **Write the failing test first**, especially for bug fixes. "Write a failing test that
  reproduces the issue, then fix it" is a self-closing loop; "fix the bug" is not.
- **Fixtures beat assertions about behavior.** A script that diffs output against a golden
  file gives a binary signal Claude can iterate against without your judgment.
- **Separate the writer from the tester.** Have one session write tests and another write
  the code to pass them. A fresh context improves review quality because Claude isn't
  biased toward code it just wrote.
- **Give example cases in the prompt.** "example test cases: `user@example.com` → true,
  `invalid` → false, `user@.com` → false" turns an ambiguous task into a checkable one.
- **Prefer single-test runs during iteration**, full suite at the gate. Put that
  preference in CLAUDE.md.

---

## 6. Phase gates that actually gate

A phase gate is only real if something other than Claude's own judgment decides whether it
passed. Three layers, weakest to strongest:

**Layer 1 — the written criteria.** Each phase in `PLAN.md` gets: acceptance criteria,
explicit out-of-scope list, and the exact command that proves it. Written *before*
implementation starts.

**Layer 2 — the gate skill.** A `disable-model-invocation: true` skill you invoke
manually, e.g. `/phase-gate 3`. It reads the criteria, runs the commands, and produces a
report. Because model invocation is off, Claude can't decide the phase is complete on its
own; if it tries, Claude Code blocks the call.

**Layer 3 — the deterministic block.** A `PreToolUse` hook that refuses writes to the
phase sign-off file, or a Stop hook that won't let the turn end until the suite passes.
This is the only layer that holds regardless of what Claude decides.

**The contamination trap.** The most common way a phase gate fails silently is that the
metrics in the report were produced by the same run that's being evaluated. Guard against
it explicitly:

- Acceptance numbers come from a command in `PLAN.md`, run at gate time, output pasted.
- The gate skill's instructions should say: *do not accept figures quoted from the
  conversation; re-run the command.*
- The reviewer subagent gets the diff and the criteria — not the implementer's summary.

**Sequencing.** Add one line to the gate skill: *verify that every prior phase's gate
report exists and passed before evaluating this one.* Cheap, and it catches the failure
where phase 4 quietly depends on something phase 2 deferred.

**Sign-off artifact.** Write `gates/phase-N.md` with: date, commit SHA, command run,
output, reviewer findings, and your explicit sign-off line. Commit it. This is what makes
the history auditable months later, and it's what a human gate means in practice — a file
only you write.

---

## 7. Context hygiene

The habits that keep a long project from degrading:

- **`/clear` between unrelated tasks.** Not optional. The kitchen-sink session is the most
  common quality killer.
- **The two-correction rule.** If you've corrected Claude twice on the same issue, the
  context is polluted with failed approaches. `/clear` and rewrite the prompt incorporating
  what you learned. A clean session with a better prompt almost always outperforms a long
  session with accumulated corrections.
- **`Esc` to interrupt** the moment you see it going wrong — context is preserved, so you
  can redirect immediately. Correcting early beats correcting thoroughly.
- **`/rewind` (or `Esc Esc`)** to restore conversation state, code state, or both. This
  makes risky experiments cheap: try it, rewind if it fails. Caveat: checkpoints only
  track changes made through Claude's file editing tools — **Bash-driven changes aren't
  captured**, so this is not a git substitute.
- **`/compact <instructions>`** for directed compaction: `/compact focus on the API
  changes`. You can also put standing compaction instructions in CLAUDE.md, like *"when
  compacting, always preserve the full list of modified files and any test commands."*
- **`/btw`** for side questions — the answer appears in a dismissible overlay and never
  enters conversation history.
- **Subagents for all investigation.** "Use subagents to investigate how X works" keeps
  hundreds of file reads out of your main window.
- **Name your sessions** with `/rename` and treat them like branches: `oauth-migration`,
  `phase3-escalation`. Resume with `claude --continue` or `claude --resume`.

---

## 8. Scaling up

Once one session is running well:

**Writer/Reviewer across two sessions.** Session A implements; session B reviews with
fresh context; you paste B's findings back to A. Fresh context improves review because the
reviewer isn't attached to the code.

**Worktrees for parallelism.** Separate git checkouts so parallel sessions don't collide
on the same files.

**Fan-out for migrations.** Have Claude write the task list to a file, then loop:

```bash
for file in $(cat files.txt); do
  claude -p "Migrate $file from X to Y. Return OK or FAIL." \
    --allowedTools "Edit,Bash(git commit *)"
done
```

Refine the prompt on the first 2–3 files before running at scale. `--allowedTools` matters
here because nobody's watching.

**Non-interactive in CI.** `claude -p "prompt" --output-format json` for pre-commit hooks
and pipelines.

---

## 9. Failure patterns to recognize early

| Pattern | Symptom | Fix |
|---|---|---|
| Kitchen sink session | Context full of three unrelated tasks | `/clear` between tasks |
| Correction spiral | Same mistake after two corrections | `/clear`, rewrite the prompt |
| Over-specified CLAUDE.md | Claude ignores rules you definitely wrote | Prune ruthlessly; convert must-haves to hooks |
| Trust-then-verify gap | Plausible code that fails on edge cases | Never ship what you can't verify |
| Infinite exploration | "Investigate X" → hundreds of files read | Scope narrowly or delegate to a subagent |
| Self-graded gate | Phase report cites metrics from its own run | Re-run the command at gate time; reviewer sees diff only |

---

## 10. Bootstrap checklist

First 30 minutes on a new project:

- [ ] `README.md` written
- [ ] `/init`, then cut the generated CLAUDE.md to the things Claude can't infer
- [ ] `/context` — confirm CLAUDE.md appears under **Memory files**
- [ ] One permission allowlist entry, one deny rule
- [ ] `SPEC.md` via the interview prompt, in its own session
- [ ] `PLAN.md` with phases, acceptance criteria, and explicit out-of-scope
- [ ] One verification command that returns pass/fail, documented in CLAUDE.md
- [ ] `.claude/agents/plan-reviewer.md`
- [ ] `.claude/skills/phase-gate/SKILL.md` with `disable-model-invocation: true`
- [ ] `.gitignore` covers `CLAUDE.local.md` and `.claude/settings.local.json`
- [ ] Fresh session to begin phase 1

Add later, when the pain appears:

- [ ] `.claude/rules/*.md` when CLAUDE.md crosses ~200 lines
- [ ] Stop hook when you start leaving runs unattended
- [ ] Skills for anything you've now typed twice
- [ ] Worktrees when you want two phases in flight

---

## 11. Develop the intuition

These are starting points, not laws. Sometimes you *should* let context accumulate because
you're deep in one problem and the history is genuinely valuable. Sometimes skip planning
because the task is exploratory. Sometimes a vague prompt is exactly right because you
want to see how Claude frames the problem before you constrain it.

Pay attention to what works. When output is great, notice what you did — the prompt
structure, the context provided, the mode you were in. When it struggles, ask why: context
too noisy, prompt too vague, or task too big for one pass?

---

## Sources

- Best practices: https://code.claude.com/docs/en/best-practices
- Memory and CLAUDE.md: https://code.claude.com/docs/en/memory
- Skills: https://code.claude.com/docs/en/skills
