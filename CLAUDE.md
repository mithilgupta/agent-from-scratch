# Notes for Claude

Read [WORKFLOW.md](WORKFLOW.md) before building anything. In short:

- Phase N's notebooks import only `agent_v(N-1)` (frozen prod code from the
  previous phase folder). Never import the current phase's prod package.
- Build every new piece in the notebook: import the old function, then write
  the new version there, step by step. Shadow imported functions; never patch
  the module.
- Write `agent_vN/` only after the whole phase works in the notebooks, as a
  deliberate refactor; then run the notebook's end-to-end demo against it.
- Each phase folder has three parts: `phase_N_README.md` (the phase's detailed doc,
  kept up to date as it's built), the notebooks, and `agent_vN/`.
- Earlier phases' packages are frozen. Fix forward, never back-port.
- The user is learning: go one step at a time and explain before racing
  ahead. Commit or push only when asked.

Environment: notebooks use the `agents` Jupyter kernel; run code and tests
with `/opt/anaconda3/envs/agents/bin/python` (the system `python3` is 3.9 and
lacks the packages).

[ROADMAP.md](ROADMAP.md) has the build order and status.
