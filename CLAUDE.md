# Notes for Claude

**Every piece of writing stands alone** (explicit instruction, 2026-11-24):
chat replies, game plans, notebook cells, READMEs. The reader must never
have to open ROADMAP.md or another cell to follow it. Never write "step 5",
"step 6", "decision 1", "question 4" or "2a above" alone; say what it is in
the same sentence, e.g. "the approval prompt (you OK each risky action
before it runs; roadmap step 5)". Mark hypothetical names as hypothetical.

Read [WORKFLOW.md](WORKFLOW.md) before building anything. In short:

- Phase N's notebooks import only `agent_v(N-1)` (frozen prod code from the
  previous phase folder). Never import the current phase's prod package.
- Build every new piece in the notebook: import the old function, then write
  the new version there, step by step. Shadow imported functions; never patch
  the module.
- Write `agent_vN/` only after the whole phase works in the notebooks, as a
  deliberate refactor; then run the notebook's end-to-end demo against it.
- Each phase folder has four parts: the notebooks (the lab: code, short
  step summaries, observations), `phase_N_research.md` (the full game plans
  and evidence, one file per phase), `agent_vN/` and `phase_N_README.md`.
- Don't update the phase README while the phase is in progress. Write it
  once, after the notebook works end to end and `agent_vN/` is refactored:
  the final write-up of what was built, the decisions and why, with evidence
  links.
- Earlier phases' packages are frozen. Fix forward, never back-port.
- **Every roadmap step starts with a game plan, agreed before any code.**
  It lives in two places (explicit instruction, 2026-11-26: the notebook
  must stay easy to read):
  - **The full plan** is a section of the phase's single research file,
    `phase-N-.../phase_N_research.md` (`## Step N: <name>`), not one file
    per step. The user reviews and agrees it there.
  - **The notebook** gets one short markdown cell at the top of the step's
    section (~15–20 lines): goal, breakdown in a sentence or two, what was
    chosen and dropped, decisions if still open, done when, and a link to
    the research section. Nothing else.
  - **Scale the research to the step:** a step that adds one small function
    gets a lighter plan than a big design choice. The real-agents table
    stays every time; a small step can skip the "by question" table and
    keep rows short.

  The full plan, in this order (explicit instruction, 2026-11-24: "we do
  this each time"):
  1. **What we're doing and why**, in two parts:
     - **The goal in one sentence**, at a high level, and which part of
       the phase's goal it serves. Keep the step's complexity in line with
       that goal (explicit instruction, 2026-11-24): no formal scoping
       exercise per phase, just this check every step.
     - **The problem broken down (MECE)**, as small tables (e.g. by
       action: read / write; by channel: our tools / terminal commands),
       each part tied to our code (file:line) and marked live today or
       not yet. This pins down what matters and keeps out the minutiae.
  2. **Evidence: how real agents do it**: the literature review, as below.
  3. **Proposed sub-steps and decisions, derived top-down with the chain
     shown:** the options the research gives (grouped, e.g. by who
     enforces) → filter by this project's level of complexity, saying
     what's dropped and why → what's left is settled (agents agree), a
     decision for the user (they differ), or a sub-step. Sub-steps get a
     "Based on" column. Never jump from research to a list.
  4. **Coverage check:** read the MECE breakdown against the proposed
     sub-steps, one row per part of the breakdown: which sub-step covers
     it, or why it's deferred or dropped. Nothing left unaccounted for.
  5. **Done when.**

  Anything without a source is labeled as Claude's judgment. Never pull
  sub-steps from memory unannounced. Draft it, let the user question and
  change it, and write no code until they agree. Model: step 3 (folder
  boundary) in `phase-1-mvp/phase_1_research.md`, and its short cell in
  `phase-1-mvp/phase_1_agent.ipynb`.
- **Every game plan includes a "How real agents do it" table**, wherever it
  can apply. The user values this most ("this is GOLD"). Read the real
  agents' source during the step (never describe them from memory), one row
  per agent with linked file:line, then "what they agree on → what we
  follow" and "where they differ". One table, two tiers: small-scale
  projects *and* the big five industry agents, every step: Gemini CLI,
  Codex CLI, opencode, OpenHands (read `OpenHands/software-agent-sdk`, where
  the agent lives) and Aider. Pin links to the commit SHA read. Research is
  a dated snapshot: never go back to re-check or update links in earlier
  steps. Closed
  agents only via public docs, labeled. The notebook is how we do it; the table is how
  everyone else does. Model: step 3 in `phase-1-mvp/phase_1_research.md`.
- **The user is learning. "Step by step" means one sub-step per turn:**
  - **A sub-step is a feature: something the agent gains** (explicit
    instruction, 2026-11-24). Testing that feature (offline checks *and*
    trying it with the model) is part of the same sub-step and cell, never
    a sub-step of its own. A question that needs many runs to answer is an
    experiment: queue it for the benchmark (Phase 2), don't make it a
    sub-step.
  - **Cells per step: as few as possible** (explicit instruction,
    2026-11-24). The short game plan cell, then, *only when the step changes
    something that already exists*, one **as-is** cell (print the current
    code and run the same question through the model, so the learner sees
    the problem happen), then one cell per sub-step (new code, its tests,
    and the same model question again, for a before/after). A step that
    adds something brand new skips the as-is cell. The test is: as a
    learner, what would I want to see or run before this feature is added
    or changed? Explanations go in Claude's message, not extra markdown
    cells. We're not writing a book.
  - **Every build cell opens with an "Execution" header** (explicit
    instruction, 2026-11-26; the user's own idea): the cell's title line,
    then `# Execution:` and 2–4 numbered comment lines, each naming one
    concrete thing the cell adds or changes (a function, a list, a changed
    line in `ask()`). It's the meat of the cell at a glance. Model: cells
    3a, 4a and 5a in `phase-1-mvp/phase_1_agent.ipynb`.
  - **Each roadmap step has 1–3 sub-steps: as few as it needs** (explicit
    instruction, 2026-10-31). One is fine, e.g. a step that only adds a
    tool. The user is a practicing data scientist: a sub-step is a
    meaningful chunk (e.g. "build the registry, prompt, parser and
    dispatcher"), not a micro-step per function. Step 1 had 7 sub-steps,
    which was too many.
  - A roadmap step is never one turn: build one sub-step, then stop.
  - Explain the piece in plain words: what it is, why it's needed, what to
    look for when running it.
  - Then **stop**. The user runs it and asks questions; add the next piece
    only when they say to. Never write ahead "to save time", and never
    finish a section in one go.
  - Ask before writing a piece if its design isn't obvious; the user wants
    to understand choices, not receive them.
  - **One cell per sub-step** (explicit instruction, 2026-11-12). If a
    sub-step has several functions, they go in the same cell; checks too.
    Don't spread a sub-step over markdown + code + check cells: the
    notebook must stay readable and usable, not a behemoth.
  - **Keep each piece minimal.** When it rewrites a Phase N-1 function,
    start from that function and change only what the game plan says; mark
    the changed lines and describe it as "the old version plus these
    changes". No extra checks, edge cases or behavior changes the plan
    didn't ask for.
- **This is a proof of concept for understanding how agents work, not an
  enterprise app** (explicit instruction, 2026-11-12). Tool functions only
  need to work for the demo; their edge cases and polish are refined at the
  end, if ever. When testing, surface findings about agent mechanics (the
  loop, tool calling, safety boundaries, context, model behavior), not
  edge cases of a particular tool function.
- The user may have the notebook open in Jupyter, which overwrites changes
  on disk when it autosaves. After editing a notebook, tell the user to
  reload it from disk (File → Reload Notebook from Disk) before running it.
- Commit or push only when asked, with one standing exception (explicit
  instruction, 2026-11-26): **every time `phase_N_research.md` changes,
  commit and push it right away** (with the notebook if its summary cell
  changed too), because the user reads the research only in the GitHub UI.
  Check the notebook for private paths or keys before pushing, as always.

Environment: notebooks use the `agents` Jupyter kernel; run code and tests
with `/opt/anaconda3/envs/agents/bin/python` (the system `python3` is 3.9 and
lacks the packages).

[ROADMAP.md](ROADMAP.md) has the build order and status.
