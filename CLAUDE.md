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
  A markdown cell at the top of the step's section with: what we're doing and
  why; the numbered sub-steps (one piece each); the evidence behind them,
  cited (our own code with file:line, the roadmap line, and real agents'
  source files or docs actually read this session, with links); and what
  "done" looks like. Anything without a source is labeled as Claude's
  judgment. Never pull sub-steps from memory unannounced. Draft it, let the
  user question and change it, and write no code until they agree.
- **The user is learning. "Step by step" means one small piece per turn:**
  - A piece is one idea, usually 1–3 notebook cells (e.g. "print Phase 0's
    `ask()` and point out where `read_file` is hard-coded"). A roadmap step
    or notebook section is many pieces, never one turn.
  - Explain the piece in plain words: what it is, why it's needed, what to
    look for when running it.
  - Then **stop**. The user runs it and asks questions; add the next piece
    only when they say to. Never write ahead "to save time", and never
    finish a section in one go.
  - Ask before writing a piece if its design isn't obvious; the user wants
    to understand choices, not receive them.
- The user may have the notebook open in Jupyter, which overwrites changes
  on disk when it autosaves. After editing a notebook, tell the user to
  reload it from disk (File → Reload Notebook from Disk) before running it.
- Commit or push only when asked.

Environment: notebooks use the `agents` Jupyter kernel; run code and tests
with `/opt/anaconda3/envs/agents/bin/python` (the system `python3` is 3.9 and
lacks the packages).

[ROADMAP.md](ROADMAP.md) has the build order and status.
