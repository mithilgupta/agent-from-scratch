# Workflow

How each phase gets built. This is **learning first, software second**: the
notebooks are where understanding happens, and the production code is
written afterwards from what the notebooks taught.

## The shape

```
agent_v0 (frozen) ──import──► Phase 1 notebook(s) ──refactor at end──► agent_v1 (frozen)
                              build and experiment                     clean prod code
```

Each phase folder holds three things:

```
phase-0-foundation/
├── phase_0_README.md    ← the phase's detailed doc: what it builds and why
├── phase_0_agent.ipynb  ← experiments: where the phase is learned
└── agent_v0/            ← prod code: written at the end of the phase, then frozen
phase-1-mvp/
├── phase_1_README.md
├── phase_1_agent.ipynb  ← imports agent_v0 only
└── agent_v1/            ← written at the end of Phase 1, then frozen
```

Notebooks are named `phase_N_agent.ipynb`. If a phase needs more than one,
add a suffix: `phase_N_agent_2.ipynb`, or a short topic name.

**The notebook is the lab; the README and `agent_vN/` are what comes out of
it.** Everything made while working lives in the notebook: game plans,
evidence, code, observations and dead ends. The **README** is the phase's
final write-up for someone who wasn't there: what was built, the decisions
and why, with links to the evidence. It's written once, after the notebook
works end to end and `agent_vN/` has been refactored, so it describes the
prod code as it actually is. The roadmap stays the overview; detail goes in
the phase README, so it scales as phases grow.

## The rules

1. **A phase's notebooks import only the previous phase's prod package.**
   Phase 1 imports `agent_v0`, never `agent_v1`. During the phase, `agent_v1`
   doesn't exist yet.

2. **Everything new is built in the notebook.** Import the old function, look
   at it, then write the new version in the notebook step by step, so the
   change is visible. For example: import v0's `ask()`, see that it hard-codes
   `read_file`, then write a new `ask()` that uses the tool registry. The
   notebook's version becomes v1's `ask()`.

3. **Every step starts with a game plan, agreed before any code.** The first
   cell of each roadmap step's section is a markdown "game plan", in this
   order, like a design doc:
   1. **What we're doing and why:** the problem statement, grounded in our
      own code (file and line) and the roadmap.
   2. **Evidence: how real agents do it:** the literature review (below).
   3. **Sub-steps (proposed):** derived from the problem and the evidence,
      each small enough to build and run in one go, with a **"Based on"**
      column naming the evidence each follows. Anything without a source is
      labeled as judgment.
   4. **Decisions:** design choices the evidence doesn't settle, for the
      user to make.
   5. **Done when:** the acceptance criteria.

   **The evidence table** (in every step where it applies): a table
     comparing how several real agents solve this step, from their **actual
     source code**, read during the step, with links to the exact lines. One
     row per agent: what it does and where. The notebook is how *we* do it;
     the table shows how everyone else does, in **one table with two
     tiers**: small-scale projects (from-scratch tutorials and minimal
     agents) and **the big five** open-source industry agents, researched
     for every step: [Gemini CLI](https://github.com/google-gemini/gemini-cli),
     [Codex CLI](https://github.com/openai/codex),
     [opencode](https://github.com/anomalyco/opencode),
     [OpenHands](https://github.com/OpenHands/software-agent-sdk) and
     [Aider](https://github.com/Aider-AI/aider). Not every agent does every
     step, and a row saying so is a finding too. **The research is a
     snapshot**, done once when the step is written: links are pinned to the
     commit read, and are never updated afterwards. These repos change
     daily, so a table describes the agents as they were on its date; that's
     a stated limitation, not something to keep chasing. Closed agents (Claude Code, Cursor) appear only through
     their public docs, labeled as such. Then **what they agree on** (and
     so what we follow) and **where they differ** (and why). This is the
     part that goes beyond a tutorial: it shows the design space, not just
     one answer. See the step 1 game plan in `phase_1_agent.ipynb` for the
     model to follow.
   - **Done when:** how we'll know the step works.

   The sub-steps are then built one at a time, in the agreed order. If the
   plan needs to change along the way, the game plan cell is updated first.

4. **Shadow, don't patch.** To change an imported function, define a new one
   with the same name in the notebook. Never reach into the module
   (`agent_v0.read_file = ...`): the module's other functions would silently
   use the replacement, so the code you read is no longer the code that runs.

5. **Notebooks per phase: as many as the story needs.** Usually one, with a
   section per roadmap step; split into two or more where it reads better.
   Steps within a phase build on each other inside the notebooks, not through
   the prod package.

6. **The phase ends with a refactor into prod code.** Once the whole phase
   works end to end in the notebooks, design `agent_vN/` properly: which
   modules, what interfaces, what tests. This is a step of its own, not a
   copy-paste.

7. **Check the refactor is faithful.** Run the notebook's final end-to-end
   demo against `agent_vN` and confirm the same behavior. Then write the
   phase README from the notebook.

8. **Frozen means frozen.** Once a phase ends, its prod package never changes.
   A bug found later in `agent_v0` is fixed in the current phase's code, not
   back-ported.

## Why this design

- **Clean dependencies:** each phase depends only on the frozen one before it,
  so nothing breaks backwards.
- **Every phase stays runnable**, exactly as it was.
- **The diff is the lesson:** comparing `agent_v0/` with `agent_v1/` shows
  exactly what a phase added.
- **Measurement gets it for free:** Phase 2's benchmark can import any
  version and compare them on the same tasks.
- **The last phase's package is the finished agent.**

## Practical details

- Package names are versioned (`agent_v0`, `agent_v1`, ...) because phase
  folder names contain hyphens and can't be imported, and so that two versions
  never collide.
- Notebooks make a previous phase importable with an explicit `sys.path` line
  pointing at its folder.
- Tests live inside the package (`agent_vN/tests/`), are frozen with it, and
  never call the model. Run them with `pytest phase-N-.../agent_vN`.
