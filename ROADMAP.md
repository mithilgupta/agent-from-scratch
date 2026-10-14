# Roadmap

The plan for this project, organized around the **problems an agent has to
solve**, not around any particular product's feature list. Nothing is
prioritized yet; the order of steps gets decided later.

## The mental model

> **Agent = Model + Harness**

| Layer | What it is |
|---|---|
| **Model** | The function `f(text) → text`. Everything it knows and how it behaves was set during training. |
| **Harness** | All the ordinary code around the model: the loop, the tools, what goes into the prompt, what gets saved, what's allowed. |

The model never acts on its own; it only produces text. The harness turns that
text into actions, feeds results back, and decides what the model gets to see
next. Claude Code, Codex CLI and Aider are mostly harnesses around someone
else's model.

```
                    ┌─────────────────── HARNESS ───────────────────┐
                    │                                                │
  You ─► Interface ─┼─► Context ─► MODEL ─► Control loop ─► Action ──┼─► your files,
                    │      ▲                     │            │      │   shell, web
                    │      │                     ▼            ▼      │
                    │   Memory ◄────────── results, history ◄─┘      │
                    │                                                │
                    │   Safety wraps every action                    │
                    │   Orchestration runs several of these at once  │
                    │   Evaluation watches all of it                 │
                    └────────────────────────────────────────────────┘
```

**Scope** (judged against this project's goal: a small, understandable demo of how agents work):

- **Core**: essential to understanding agents; candidates for the MVP
- **Later**: teaches something real, but not needed for the basics; candidates for later iterations
- **Skip**: product polish, packaging or infrastructure; matters in real products, teaches little about agents

**Status:** ✅ built · ⬜ not yet

---

# Build order (Core)

The order to build the Core components in, grouped into phases. Two rules
decide it: **dependencies first** (for example, ask permission before giving
the agent a shell), and **get to a working coding agent early, then measure
it before making big changes**, so each later change can be judged by results.

### Phase 0: Foundation (step 01)

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| — | Agent loop | Control loop | The core of every agent | ✅ |
| — | Step limit | Control loop | Stops a confused model from looping forever | ✅ |
| — | Read file | Tools | The first, simplest tool | ✅ |
| — | System prompt | Context | How the model learns the tool exists | ✅ |
| — | Conversation history | Memory | Makes follow-up questions work | ✅ |

### Phase 1: MVP, a coding agent that can fix a bug safely

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| 1 | Tool registry | Tools | Set this up before adding tools, so each new tool is a function, not a prompt rewrite | ⬜ |
| 2 | List and find files | Tools | The agent has to explore a project before it can change it | ⬜ |
| 3 | Folder boundary | Safety | Keep file tools inside the project before any of them can write | ⬜ |
| 4 | Write and edit files | Tools | The moment the agent can actually change code | ⬜ |
| 5 | Approval prompt | Safety | Ask before risky actions, needed before shell access | ⬜ |
| 6 | Run shell commands | Tools | Lets the agent run code, tests and git | ⬜ |
| 7 | Verify loop | Control loop | Run the tests, fix what fails, repeat: this is what makes it a *coding* agent | ⬜ |

**MVP done when:** given a small project with a failing test, the agent finds
the bug, fixes it, runs the tests to confirm, and asks before anything risky.

### Phase 2: See and measure it

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| 8 | Run log | Evaluation | Record every call and tool result so runs can be inspected | ⬜ |
| 9 | Token and cost tracking | Evaluation | Know what each run costs before making it bigger | ⬜ |
| 10 | Task benchmark | Evaluation | A small fixed set of tasks to score every later change against | ⬜ |
| 11 | Same harness, different models | Model | First use of the benchmark: how much does the model matter? | ⬜ |

### Phase 3: Make it robust and well-informed

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| 12 | Native tool calling | Tools | Replace text parsing with structured tool calls | ⬜ |
| 13 | Text protocol vs native tool calling | Model | Measure what step 12 bought, on the benchmark | ⬜ |
| 14 | Environment info | Context | Tell the agent where it is: folder, OS, date, git status | ⬜ |
| 15 | Project instructions file | Context | Project conventions loaded at startup | ⬜ |

### Phase 4: Handle longer tasks

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| 16 | To-do list | Control loop | Keep multi-step tasks on track | ⬜ |
| 17 | Plan mode | Control loop | Explore and plan before editing; builds on the approval prompt and the to-do list | ⬜ |
| 18 | Compaction | Context | Long tasks fill the context window; summarize to make room | ⬜ |
| 19 | Long-term notes | Memory | Remember things across sessions | ⬜ |

### Phase 5: Multiple agents

| # | Component | Topic | Why here | Status |
|---|---|---|---|---|
| 20 | Subagents | Orchestration | Delegate a side task to a fresh agent; keep only its summary | ⬜ |
| 21 | Specialized agents | Orchestration | Explore, plan and review agents with their own tools and prompts; builds on subagents | ⬜ |

---

# Part 1: The harness

Eight topics. Each answers one question the harness has to get right.

## 1. Control loop and planning

**The question:** How does the agent decide what to do next, and when to stop?

**Why it matters:** The loop is the agent. Without structure, models wander
on long tasks, stop halfway, or never stop at all.

**Key ideas:** the agent loop; stopping conditions; planning before acting;
checking your own work.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Agent loop | Call model → tool requested? → run it → feed result back → repeat | Core | ✅ |
| Step limit | A cap on iterations so a confused model can't loop forever | Core | ✅ |
| To-do list | The model writes a checklist and ticks items off as it goes | Core | ⬜ |
| Plan mode | Explore read-only first, propose a plan, edit only after approval | Core | ⬜ |
| Verify loop | Run tests or lint after a change and fix what fails | Core | ⬜ |
| Goal check | A separate check decides whether the task is truly done | Later | ⬜ |
| Loop detection | Notice the agent repeating itself and stop it | Later | ⬜ |
| Retries | Recover from failed model calls without losing progress | Skip | ⬜ |

## 2. Action (tools)

**The question:** What can the agent do, and how should those abilities be designed?

**Why it matters:** Tools are the agent's only way to affect the world. The
model sees nothing but each tool's name, description and inputs, so tool
design is interface design for a reader that can't ask questions.

**Key ideas:** the core toolset (read, write, edit, search, run); describing
tools to the model; text-protocol vs native tool calling; returning errors as
information; keeping outputs a manageable size.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Read file | See a file's contents | Core | ✅ |
| List and find files | Explore a project's structure | Core | ⬜ |
| Write and edit files | Create files; replace an exact snippet, failing clearly if it isn't found | Core | ⬜ |
| Search contents | Find code by pattern across a project | Later | ⬜ |
| Run shell commands | Run tests, scripts and git; read the output | Core | ⬜ |
| Web fetch and search | Read docs and look up errors | Later | ⬜ |
| Ask the user | Ask a clarifying question mid-task instead of guessing | Later | ⬜ |
| Tool registry | Describe tools automatically from their code; add a tool without touching the loop | Core | ⬜ |
| Native tool calling | The API returns structured tool requests instead of us parsing text | Core | ⬜ |
| Parallel tool calls | Run several requested tools from one reply | Later | ⬜ |
| Large output handling | Truncate huge results and keep the full version somewhere retrievable | Later | ⬜ |
| Edit formats | Compare whole-file rewrites, search-and-replace and diffs as ways to edit | Later | ⬜ |
| Code intelligence | Report type errors after edits; jump to definitions | Skip | ⬜ |
| Bash-only agent | The minimalist alternative: one shell tool instead of many | Later | ⬜ |

## 3. Context

**The question:** Out of everything available, what goes into the prompt on *this* call?

**Why it matters:** The model only knows what's in front of it, and space is
limited. Too little and it guesses; too much and it gets slow, expensive and
distracted. Deciding what goes in is called **context engineering**.

**Key ideas:** the context window as working memory; system prompts;
always-on vs on-demand information; summarizing to make room.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| System prompt | Instructions that shape how the agent works | Core | ✅ |
| Environment info | The working directory, OS, date and git status, so the agent knows where it is | Core | ⬜ |
| Project instructions file | An `AGENTS.md`-style file with project conventions, loaded at startup | Core | ⬜ |
| Repo map | A compact outline of a codebase's key classes and functions | Later | ⬜ |
| Pinning files | Let the user add specific files to the conversation | Skip | ⬜ |
| Context meter | Show how full the context window is, and with what | Later | ⬜ |
| Compaction | When space runs low, drop old tool outputs, then summarize history | Core | ⬜ |
| Skills | Task-specific instructions loaded only when relevant | Later | ⬜ |
| Prompt caching | Reuse the unchanged start of the prompt to save cost and time | Skip | ⬜ |

## 4. Memory

**The question:** What does the agent keep, and for how long?

**Why it matters:** The model forgets everything between calls. Anything that
should last, whether for the next call, the next session or forever, has to
be stored by the harness.

**Key ideas:** memory is what's *stored*; context (topic 3) is what's
*selected* from it for one call. Memory ranges from the current conversation
up to facts kept across sessions.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Conversation history | Resend everything said so far, so follow-ups work | Core | ✅ |
| Saved sessions | Write each conversation to disk | Later | ⬜ |
| Resume and fork | Continue an old session, or branch off from it | Skip | ⬜ |
| Long-term notes | The agent saves facts worth remembering and loads them next time | Core | ⬜ |
| Memory upkeep | Decide what's worth keeping; merge and prune over time | Later | ⬜ |
| Retrieval | Search past sessions and pull back only the relevant parts | Later | ⬜ |

## 5. Safety and control

**The question:** What is the agent allowed to do, and how do we undo its mistakes?

**Why it matters:** An agent that can edit files and run commands can also
delete them. Safety is what makes it reasonable to let it act on its own.

**Key ideas:** asking before acting; rules about what's allowed; isolating
where actions run; making changes reversible; treating content the agent
reads as data, never as instructions.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Approval prompt | Ask "allow this?" before risky actions | Core | ⬜ |
| Permission rules | Allow / ask / deny rules per tool and pattern | Later | ⬜ |
| Permission modes | Switch between ask-everything, accept-edits, read-only and auto | Skip | ⬜ |
| Automatic risk check | A model judges each action and blocks only risky ones | Later | ⬜ |
| Folder boundary | File tools can't reach outside the project | Core | ⬜ |
| Sandbox | Run commands where they can't touch the real machine (restricted shell, container, cloud) | Later | ⬜ |
| Checkpoints | Snapshot files before each edit so they can be rolled back | Later | ⬜ |
| Git safety net | Commit each change automatically; undo with one command | Skip | ⬜ |
| Isolated workspaces | Each task works on its own copy of the repo | Skip | ⬜ |
| Prompt-injection defense | Don't obey instructions hidden in files or web pages | Later | ⬜ |

## 6. Orchestration

**The question:** How is work split across several agents or models?

**Why it matters:** One conversation can only hold so much. Handing a side
task to a fresh agent keeps the main context clean; running agents in
parallel gets more done; cheaper models can handle easier work.

**Key ideas:** subagents are mostly a context-management tool; delegation
vs collaboration; matching model size to task difficulty.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Subagents | Hand off a sub-task to a fresh agent; keep only its summary | Core | ⬜ |
| Specialized agents | Explore, plan, build and review agents with different tools and prompts | Core | ⬜ |
| Parallel agents | Several subagents working at once | Later | ⬜ |
| Background work | Long tasks run in the background and report back | Skip | ⬜ |
| Agent teams | Agents sharing a task list and messaging each other | Skip | ⬜ |
| Scripted workflows | Code that coordinates many agents in a fixed pattern | Skip | ⬜ |
| Model routing | A cheap model for easy work, a strong one for hard decisions | Later | ⬜ |

## 7. Evaluation and observability

**The question:** Does it work, what did it do, and what did it cost?

**Why it matters:** Without measurement you can't tell whether a new
component helped or hurt. This is the most data-science-like part of the
project, and the part most tutorials skip.

**Key ideas:** logging every step; test sets of tasks; comparing versions;
tracking tokens and dollars.

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Run log | Record every model call and tool result | Core | ⬜ |
| Token and cost tracking | Tokens and dollars per call and per session | Core | ⬜ |
| Run viewer | Browse a past run step by step | Skip | ⬜ |
| Fake model for tests | Test the harness deterministically and for free | Later | ⬜ |
| Task benchmark | A fixed set of tasks to score each version of the agent | Core | ⬜ |
| Record and replay | Re-run a failed run with a different prompt or model | Skip | ⬜ |
| Capstone task | One real job the finished agent completes end to end | Later | ⬜ |

## 8. Interfaces and integration

**The question:** How do people and other systems work with the agent?

**Why it matters:** The same harness can serve a person at a terminal, a
script in CI, or another program. And extension points let others add
abilities without changing the core.

**Key ideas:** human-in-the-loop vs fully automatic use; extension points
(hooks, plugins, MCP).

| Component | What it adds | Scope | Status |
|---|---|---|---|
| Terminal chat | Type, read the reply, repeat | Later | ⬜ |
| Streaming | Show replies as they're written | Later | ⬜ |
| Interrupt and steer | Stop or redirect the agent mid-task | Skip | ⬜ |
| Diff preview | Show a change before it's applied | Later | ⬜ |
| Slash commands | `/help`, `/clear`, `/model` and user-defined shortcuts | Skip | ⬜ |
| Status line | Model, context use and cost always visible | Skip | ⬜ |
| Headless mode | One-shot runs from scripts, with structured output | Skip | ⬜ |
| Library and HTTP API | Use the agent from other code or over the network | Skip | ⬜ |
| Hooks | Run your own code before or after the agent's actions | Later | ⬜ |
| MCP | Connect external tool servers through the Model Context Protocol | Later | ⬜ |
| Plugins | Bundle tools, skills, hooks and commands to share | Skip | ⬜ |
| Integrations | GitHub (issue to pull request, code review), chat apps, scheduled runs | Skip | ⬜ |

---

# Part 2: The model

**The question:** What's inside `f()`, and how does it shape what the harness needs?

**Why it matters:** The harness can be small because modern models are
*trained* to plan, call tools and follow instructions. Swap the model and the
same harness can behave very differently.

This part is about **experiments, not building**: we use models; labs make them.

**Key ideas, in the order models are made:**

| Stage | What it gives the model |
|---|---|
| Pretraining | Knowledge and language, from predicting the next word over huge amounts of text |
| Instruction tuning | Following instructions and holding a conversation |
| Reinforcement learning from feedback (alignment) | Being helpful, honest and safe in the way people prefer |
| Reasoning training | Thinking step by step before answering ("reasoning" or "thinking" models) |
| Tool-use and agentic training | Calling tools reliably and working through long tasks |

| Experiment | What it shows | Scope | Status |
|---|---|---|---|
| Same harness, different models | How much of an agent's quality comes from the model vs the harness | Core | ⬜ |
| Small vs large model | Where small models break: format errors, lost track of the task, bad tool calls | Later | ⬜ |
| Reasoning on vs off | What thinking buys on hard tasks, and what it costs | Later | ⬜ |
| Text protocol vs native tool calling | How much tool-use training matters | Core | ⬜ |
| Fine-tuning a small model *(stretch)* | Teaching a small model our tool format | Skip | ⬜ |

---

# Cutting across everything

Two concerns show up in every topic:

- **Cost and speed.** Every component trades tokens and waiting time for quality. Each step should note what it costs.
- **Reliability.** Each component adds a way to fail. Each step should show its failure modes, not just its happy path.

# How the topics connect

- **Memory feeds Context:** memory is the library, context is the books on the desk for this one call.
- **The Control loop drives Action**, and **Safety wraps every Action**.
- **Orchestration** runs several loops, each with its own context.
- **Interfaces** are how the loop gets its input and shows its output.
- **Evaluation** measures all of it, including how much depends on **the Model**.

# Further reading

- Lilian Weng, ["LLM Powered Autonomous Agents"](https://lilianweng.github.io/posts/2023-06-23-agent/) (2023): the classic framing of an agent as model + planning + memory + tool use
