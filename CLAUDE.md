# Notes for Claude

Read [WORKFLOW.md](WORKFLOW.md) before building anything. In short:

- Phase N's notebooks import only `agent_v(N-1)` (frozen prod code from the
  previous phase folder). Never import the current phase's prod package.
- Build every new piece in the notebook: import the old function, then write
  the new version there, step by step. Shadow imported functions; never patch
  the module.
- Write `agent_vN/` only after the whole phase works in the notebooks, as a
  deliberate refactor; then run the notebook's end-to-end demo against it.
- Each phase folder has three parts: the notebooks (the lab: game plans,
  evidence, code, observations), `agent_vN/` and `phase_N_README.md`.
- Don't update the phase README while the phase is in progress. Write it
  once, after the notebook works end to end and `agent_vN/` is refactored:
  the final write-up of what was built, the decisions and why, with evidence
  links.
- Earlier phases' packages are frozen. Fix forward, never back-port.
- **Every roadmap step starts with a game plan cell, agreed before any code.**
  A markdown cell at the top of the step's section, in this order:
  (1) what we're doing and why, the problem statement (our code with
  file:line, the roadmap line); (2) evidence: how real agents do it, the
  literature review (source actually read this session, with links);
  (3) proposed sub-steps derived from 1 and 2, one piece each, with a
  "Based on" column; (4) decisions for the user; (5) done when. Anything without a source is labeled as Claude's
  judgment. Never pull sub-steps from memory unannounced. Draft it, let the
  user question and change it, and write no code until they agree.
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
  everyone else does. Model: the step 1 game plan in
  `phase-1-mvp/phase_1_agent.ipynb`.
- **The user is learning. "Step by step" means one sub-step per turn:**
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
  - **Keep each piece minimal.** When it rewrites a Phase N-1 function,
    start from that function and change only what the game plan says; mark
    the changed lines and describe it as "the old version plus these
    changes". No extra checks, edge cases or behavior changes the plan
    didn't ask for.
- The user may have the notebook open in Jupyter, which overwrites changes
  on disk when it autosaves. After editing a notebook, tell the user to
  reload it from disk (File → Reload Notebook from Disk) before running it.
- Commit or push only when asked.

Environment: notebooks use the `agents` Jupyter kernel; run code and tests
with `/opt/anaconda3/envs/agents/bin/python` (the system `python3` is 3.9 and
lacks the packages).

[ROADMAP.md](ROADMAP.md) has the build order and status.
