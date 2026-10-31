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

The **README** is the detailed doc for the phase: the explanation behind the
notebooks, kept up to date as the phase is built. The roadmap stays the
overview; detail goes in the phase README, so it scales as phases grow.

## The rules

1. **A phase's notebooks import only the previous phase's prod package.**
   Phase 1 imports `agent_v0`, never `agent_v1`. During the phase, `agent_v1`
   doesn't exist yet.

2. **Everything new is built in the notebook.** Import the old function, look
   at it, then write the new version in the notebook step by step, so the
   change is visible. For example: import v0's `ask()`, see that it hard-codes
   `read_file`, then write a new `ask()` that uses the tool registry. The
   notebook's version becomes v1's `ask()`.

3. **Shadow, don't patch.** To change an imported function, define a new one
   with the same name in the notebook. Never reach into the module
   (`agent_v0.read_file = ...`): the module's other functions would silently
   use the replacement, so the code you read is no longer the code that runs.

4. **Notebooks per phase: as many as the story needs.** Usually one, with a
   section per roadmap step; split into two or more where it reads better.
   Steps within a phase build on each other inside the notebooks, not through
   the prod package.

5. **The phase ends with a refactor into prod code.** Once the whole phase
   works end to end in the notebooks, design `agent_vN/` properly: which
   modules, what interfaces, what tests. This is a step of its own, not a
   copy-paste.

6. **Check the refactor is faithful.** Run the notebook's final end-to-end
   demo against `agent_vN` and confirm the same behavior.

7. **Frozen means frozen.** Once a phase ends, its prod package never changes.
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
