# Phase 1: MVP, a coding agent that can fix a bug safely

Phase 0's agent could only **read**: it could explain a bug but not fix it.
Phase 1 gives it the tools to explore, edit and run code, with safety checks
before anything risky. Open [`phase_1_agent.ipynb`](phase_1_agent.ipynb) and
run it top to bottom; the full plans and the evidence from real agents are in
[`phase_1_research.md`](phase_1_research.md).

**Goal, met on 2026-11-26:** given a small project with a failing test, the
agent finds the bug, fixes it, runs the tests to confirm, and asks before
anything risky.

## The one idea to take away

> **A coding agent is the same loop as Phase 0, plus a few tools, a few places
> where the harness says "no" or "ask first", and two sentences of
> instructions.**

The model never gained a new ability in this phase. Every change was ordinary
Python around it: functions it can ask for, checks before those functions run,
and text in its prompt. The last step showed how much the text matters: with
the same tools, the model went from *asking the user for details* to *running
the full fix cycle by itself* once the prompt told it to investigate and verify.

## What was built, step by step

| # | Step | What the agent gained | The key decision, and why |
|---|---|---|---|
| 1 | **Tool registry** | Tools are plain Python functions; the prompt lists them automatically, and the parser and loop accept any registered tool | Describe each tool from the function itself (its name, parameters and docstring), so adding a tool never means rewriting the prompt. Broken tool calls go back to the model as errors instead of being mistaken for answers. |
| 2 | **Find files** | `find_files(pattern)`: explore a project by name | One glob tool, capped at 10 results with a "narrow your pattern" note, alphabetical, hidden files skipped. When the model searched only the top folder, a note in the empty result fixed it where a clearer description hadn't. |
| 3 | **Folder boundary** | File tools refuse paths outside the project | A check in our own code (resolve the path, following symlinks, then test it's under the project folder), as learn-claude-code and Gemini CLI do. Containers and OS sandboxes are out of scope for this project. |
| 4 | **Edit files** | `edit_file(filename, old_text, new_text)` | Find-and-replace, the format nearly every tool-calling agent uses: the old text must match exactly and appear once, with separate errors for "not found" and "found N times". No tool to create files yet; the goal didn't need one. |
| 5 | **Approval prompt** | Every edit (and later every command) waits for your yes | Asked before every change, not only when a rule flags danger: the agents that skip asking (Codex, Aider, OpenHands) have an OS sandbox, git undo or a container behind them; this agent has none. Press Enter to allow, or type a reason to refuse, and the model receives the reason. |
| 6 | **Run shell commands** | `run_command(command)`: run tests and see the output | A fresh process per command in the project folder, a fixed 30-second limit, the exit code plus output, every command approved. A command can reach outside the project, which the folder check can't stop; the approval prompt is the guard there, a known limitation. |
| 7 | **Verify loop** | The agent investigates, fixes and re-runs the tests until they pass | A two-part instruction in the system prompt, as every industry agent does it, rather than forcing the check in the loop (as Aider can) or asking a second model to judge. |

Each step's plan, the comparison with eight real agents (read from their
source, with links pinned to the commit read) and the options dropped are in
the research doc: steps [3](phase_1_research.md#step-3-folder-boundary),
[4](phase_1_research.md#step-4-write-and-edit-files),
[5](phase_1_research.md#step-5-approval-prompt),
[6](phase_1_research.md#step-6-run-shell-commands) and
[7](phase_1_research.md#step-7-verify-loop). Steps 1 and 2 were planned
before that file existed; their plans are in the notebook.

## What we found

Each is one or two live runs: observations, not measurements. The ones worth
measuring are queued as experiments for Phase 2's benchmark in
[`ROADMAP.md`](../ROADMAP.md#phase-2-see-and-measure-it).

- **Without instructions, the model acts like a chat assistant.** Asked *"The
  tests fail. Fix the bug."* with the original prompt, it used no tools and
  asked the user which tests fail and what the error was. With two added
  sentences (investigate with your tools; re-run the tests until they pass), it
  ran the tests, read the code, fixed it and ran the tests again.
  ([Step 7 result](phase_1_research.md#result-live-run-2026-11-26-1))
- **A refusal stops the action, not the goal.** After a bare "no" to
  `cat ../ROADMAP.md`, the model went straight to `read_file`, then three
  searches, until the step limit ended the run. After a refusal *with a reason*
  ("too risky"), it stopped and asked. Every layer was needed: the approval
  prompt, the folder check, a search confined to the project, the step limit.
  ([Step 6 result](phase_1_research.md#result-live-run-2026-11-26))
- **Refusals were handled honestly.** Refused by the folder check or by the
  user, the model never claimed the action had happened.
- **Check with code, not with the model's word.** Asked to show what the test
  command printed, it said the tests "passed" without quoting the output. It was
  right; the cell's own check (run the tests again, compare the test file) is
  what showed it.
- **Feedback in a result beats a better description.** When `find_files`
  searched only the top folder, rewording the tool's description didn't change
  the model's behaviour; a note in the empty result did.

## Limitations (what later phases might fix)

- **A shell command can reach anything your user account can.** The folder
  check covers only our file tools; the approval prompt is the only guard for
  commands. An OS sandbox would close this, and is out of scope.
- **Tool calls are still parsed from text, one line each.** A tool call split
  over several lines is mistaken for a final answer → Phase 3 (native tool
  calling).
- **No search inside files.** On a bigger codebase the agent would have to
  guess file names; it can run `grep` through the shell instead.
- **No tool to create files**, so the agent can't add a new test.
- **Stale bytecode:** if a file is edited in the same second as a test run,
  Python may reuse the old compiled version and report a wrong failure. Human
  approvals add enough delay that it never happened in a live run.
- **`conversation` still grows forever** → Phase 4 (compaction).

## Prod code: `agent_v1`

The notebook's final code, moved into a frozen package,
[`agent_v1/`](agent_v1/), so Phase 2 can import it (see
[WORKFLOW.md](../WORKFLOW.md)). Comparing it with
[`agent_v0/`](../phase-0-foundation/agent_v0/) shows exactly what Phase 1 added.

| File | Holds |
|---|---|
| `llm.py` | `get_client()`, `call_llm()`: copied unchanged from `agent_v0`, so the package stands alone |
| `tools.py` | The registry (`TOOLS`, `register`), the folder boundary (`set_project_root`, `inside_project`), `read_file`, `find_files`, `edit_file`, `run_command`, `RISKY_TOOLS` |
| `loop.py` | The system prompt (`build_system_prompt`, `VERIFY_INSTRUCTIONS`), `parse_tool_call`, `run_tool`, `approve`, `new_conversation`, `ask` |
| `tests/` | 21 offline tests; none of them call the model |

The code is the notebook's final version, with three changes to make it a
package:

- **The folder boundary defaults to the folder Python started in**, as in real
  agents, instead of a hard-coded `sandbox/`; `set_project_root(path)` changes it.
- **The step limit defaults to 10** instead of 5: one fix cycle (run the tests,
  read, edit, run the tests again, answer) already uses 5 model calls.
- **The notebook's change markers** (`# new`, `# changed`) are gone.

```python
import sys; sys.path.insert(0, "../phase-1-mvp")
from agent_v1 import ask, new_conversation, set_project_root

set_project_root("sandbox")
conversation = new_conversation()
ask("The tests fail. Fix the bug.", conversation)
```

Run the tests with `pytest phase-1-mvp/agent_v1` from the repo root.

**Faithful check (2026-11-26):** the notebook's last cell runs the verify
loop's demo against the package instead of the notebook's code. It behaved the
same: the same four tool calls in the same order (run the tests, read
`calc.py`, edit `return a - b` to `return a + b`, run the tests again), the
test file unchanged, and the tests passing.

## Try it

Predict what happens before you run each one:

1. Ask the agent to delete a file. Which tool would it need, and does it have one?
2. Refuse an edit with a reason that suggests a different fix. Does it follow your suggestion?
3. Remove `VERIFY_INSTRUCTIONS` from the prompt and ask it to fix a bug again. Does it still check its work?
4. Ask it to run `cat ../ROADMAP.md`. What stops it, and what doesn't?
