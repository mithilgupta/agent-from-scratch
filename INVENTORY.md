# Inventory

> **Snapshot from October 2026, not maintained.** This is an aspirational,
> unsorted list of components collected from the docs of production coding
> agents and from other "build an agent from scratch" repos, kept as raw
> brainstorming material. Expect it to go out of date.

Nothing here is prioritized or scoped. The groupings below are loose, based on
where each feature showed up, not on a deeper model of how agents work.

## Legend

- **Status:** ✅ built · ⬜ backlog
- **Seen in** (where we found evidence for the component):
  - Production agents: **CC** Claude Code · **Codex** Codex CLI · **Gemini** Gemini CLI · **Aider** · **OC** OpenCode · **mini** mini-swe-agent · **OH** OpenHands
  - From-scratch tutorials: **LCC** learn-claude-code · **DAI** decodingai course · **BYO** build-your-own-coding-agent · **SD** build-coding-agent-from-scratch workshop · **GH** how-to-build-a-coding-agent workshop
  - **idea**: not found in our sources, but a natural extension

---

## A. The core loop and talking to the model

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| A1 | Minimal agent loop | Call model → tool requested? → run it → send result back → repeat | all | ✅ (step 01) |
| A2 | Conversation memory | Resend the whole history every call so follow-ups work | all · SD | ✅ (step 01) |
| A3 | Step limit | Stop after N tool calls so a confused model can't loop forever | BYO (tool-call budget) | ✅ (step 01) |
| A4 | Native tool calling | The API returns structured tool requests instead of us parsing text | CC · DAI · BYO · SD | ⬜ |
| A5 | Text-only / bash-only protocol | The opposite design: no tool-calling API, works with any model | mini | ✅ (step 01 is a version of this) |
| A6 | Parallel tool calls | Run every tool call in one model reply, not just the first | SD · CC | ⬜ |
| A7 | Streaming output | Show the reply as it's generated, not all at the end | CC (SDK streaming) | ⬜ |
| A8 | Interrupt and steer | Stop the agent mid-task, or add a correction while it works | CC · Codex | ⬜ |
| A9 | Structured outputs | Force the final answer into a JSON schema | CC (SDK) | ⬜ |
| A10 | Prompt caching | Reuse the unchanged start of the prompt to cut cost and latency | CC · Gemini · Aider | ⬜ |

## B. Tools: what the agent can do

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| B1 | Read file | Return a file's contents | all · GH · SD | ✅ (step 01) |
| B2 | List files | List a directory | GH | ⬜ |
| B3 | Write / create file | Create a new file or overwrite one | CC · BYO | ⬜ |
| B4 | Edit file (exact match) | Replace an exact snippet; fail clearly if it isn't found | CC · SD · GH · BYO | ⬜ |
| B5 | Find files (glob) | Find files by name pattern | CC | ⬜ |
| B6 | Search contents (grep) | Search inside files, e.g. with ripgrep | CC · GH | ⬜ |
| B7 | Run shell commands | Execute commands and feed back the output | all · SD · GH · BYO | ⬜ |
| B8 | Web fetch | Read a web page | CC · Gemini · DAI | ⬜ |
| B9 | Web search | Search the web for current info | CC · Codex · Gemini | ⬜ |
| B10 | Ask the user | A tool to ask a clarifying question mid-task | CC · DAI | ⬜ |
| B11 | Notebook editing | Edit Jupyter notebook cells | CC | ⬜ |
| B12 | Image input | Attach screenshots or diagrams | Codex · Aider | ⬜ |
| B13 | Code intelligence (LSP) | Type errors after edits, go-to-definition, find references | CC · OC · DAI | ⬜ |
| B14 | Background processes | Start a long command, watch its output, keep working | CC · LCC | ⬜ |
| B15 | Browser automation | Click through and test a web app | CC (Chrome) | ⬜ |

## C. Tool infrastructure: how tools are built and wired

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| C1 | Tool registry / dispatch map | Add a tool without touching the loop | LCC · BYO | ⬜ |
| C2 | Auto-generated tool descriptions | Build the tool's prompt or schema from its signature and docstring | BYO (Pydantic tool factory) | ⬜ |
| C3 | Errors as data | Tools return readable errors instead of crashing the agent | all | ✅ (step 01, partially) |
| C4 | Large output handling | Truncate huge tool results; save the full output to a file | CC | ⬜ |
| C5 | Edit formats | Compare whole-file, search/replace and diff formats for edits | Aider | ⬜ |
| C6 | Stale-file detection | Notice when a file changed on disk since the agent read it | CC | ⬜ |
| C7 | Tool search / lazy loading | With many tools, load descriptions only when needed | CC | ⬜ |
| C8 | Self-extending tools | The agent writes and hot-loads new tools at runtime | BYO | ⬜ |

## D. Context engineering: what the model sees

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| D1 | Coding system prompt | Instructions that shape *how* it works (e.g. test-first, verify) | SD · BYO | ⬜ |
| D2 | Environment context | Tell the model the working directory, OS, date, git branch and status | CC | ⬜ |
| D3 | Project instructions file | `AGENTS.md` / `CLAUDE.md` loaded at startup; `/init` generates one | CC · Codex · Gemini · OC | ⬜ |
| D4 | Repo map | Compact map of key classes and functions, ranked by how connected they are, within a token budget | Aider | ⬜ |
| D5 | Adding files to context | Let the user pin files into the conversation (`/add`, `@file`) | Aider · CC | ⬜ |
| D6 | Context usage meter | Show what's filling the context window | CC (`/context`) | ⬜ |
| D7 | Staged compaction | First clear old tool outputs, then summarize history; trigger near the limit | CC · LCC · DAI · BYO | ⬜ |
| D8 | Manual compaction with focus | `/compact focus on X` keeps what matters | CC | ⬜ |
| D9 | Injected reminders | Short notes the harness adds mid-conversation (e.g. "this file changed") | CC | ⬜ |
| D10 | Skills | Task-specific instructions; only names load at startup, full text on demand | CC · Codex · LCC · DAI · OC | ⬜ |

## E. Memory across sessions

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| E1 | Auto memory | The agent saves learnings to a file, loaded at the next startup | CC · DAI | ⬜ |
| E2 | Memory extraction and consolidation | Decide what's worth remembering; merge and prune over time | LCC | ⬜ |
| E3 | Retrieval-based memory | Embed past sessions and pull back only the relevant pieces | idea | ⬜ |

## F. Planning and control flow

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| F1 | To-do list tool | The model writes a checklist and ticks items off | CC · LCC · DAI | ⬜ |
| F2 | Task graph | Tasks with dependencies, stored in a file | CC · LCC | ⬜ |
| F3 | Plan mode | Read-only exploration, then a plan for the user to approve before edits | CC · OC · DAI | ⬜ |
| F4 | Chat modes | Separate ask / architect / code modes | Aider | ⬜ |
| F5 | Verify loop | Run lint and tests after changes and fix failures automatically | Aider · CC | ⬜ |
| F6 | Goal loop | A separate check decides when the task is truly done | CC (`/goal`) · LCC | ⬜ |

## G. Safety and permissions

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| G1 | Approval prompt | Ask "allow this?" before risky tools run | all | ⬜ |
| G2 | Permission rules | Allow / ask / deny rules with patterns (e.g. allow `pytest`, deny `rm`) | CC · LCC · DAI | ⬜ |
| G3 | Permission modes | Manual, accept-edits, plan-only and auto modes | CC · Codex · OC | ⬜ |
| G4 | Auto-approve classifier | A model judges each action and blocks only the risky ones | CC (auto mode) | ⬜ |
| G5 | Read-only command allowlist | Safe commands (`ls`, `git status`) run without asking | CC | ⬜ |
| G6 | Working-directory boundary | File tools can't reach outside the project without permission | CC | ⬜ |
| G7 | Trusted folders | Only run with full power in folders you've marked trusted | Gemini | ⬜ |
| G8 | Sandboxed shell | Limit which files and network hosts commands can reach | CC · Codex · Gemini | ⬜ |
| G9 | Container / remote sandbox | Run tools in Docker or a cloud sandbox instead of your machine | DAI · mini · BYO | ⬜ |
| G10 | Prompt-injection awareness | Treat file and web content as data, not instructions | idea | ⬜ |

## H. Undo and recovery

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| H1 | Checkpoints and rewind | Snapshot files before each edit; roll back | CC · Gemini | ⬜ |
| H2 | Git integration | Auto-commit each change with a message; `/undo` reverts it | Aider · OC | ⬜ |
| H3 | Worktree isolation | Each task works in its own git worktree | CC · LCC | ⬜ |
| H4 | Thrash / loop detection | Notice the agent repeating itself and stop | CC (compaction thrashing) | ⬜ |
| H5 | Retries and fallbacks | Retry failed model calls; fall back to another model | idea | ⬜ |

## I. Sessions

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| I1 | Save sessions to disk | Persist every message and tool call (JSONL file or SQLite) | CC · BYO | ⬜ |
| I2 | Resume / continue | Reopen a past session | CC · Codex | ⬜ |
| I3 | Fork a session | Copy the history into a new branch of the conversation | CC | ⬜ |
| I4 | Export / share | Export or share a transcript | CC · OC | ⬜ |

## J. Multiple agents

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| J1 | Subagents | Hand a sub-task to a fresh agent; keep only its summary | CC · Codex · LCC · DAI | ⬜ |
| J2 | Specialized agents | Explore / plan / build / review agents with different tools and prompts | DAI · OC | ⬜ |
| J3 | Parallel subagents | Several subagents at once | DAI · CC | ⬜ |
| J4 | Background tasks with notifications | Long work runs in the background and reports back | LCC · CC | ⬜ |
| J5 | Agent teams | Persistent teammates sharing a task list and messaging each other | CC · LCC | ⬜ |
| J6 | Scripted workflows | Code that orchestrates many agents, resumable from a journal | CC · LCC | ⬜ |
| J7 | Advisor model | A stronger model consulted at key decisions | CC | ⬜ |
| J8 | Model routing | Cheap model for background and subagent work, strong model for the main task | CC | ⬜ |

## K. Extensibility

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| K1 | Hooks | Run your code before or after tool calls and other events | CC · LCC · BYO | ⬜ |
| K2 | MCP client | Connect to external tool servers through the Model Context Protocol | CC · Codex · Gemini · OC · LCC | ⬜ |
| K3 | Custom slash commands | User-defined shortcuts like `/review` | Gemini · OC · CC | ⬜ |
| K4 | Plugins / extensions | Package tools, skills, hooks and commands together to share | CC · Gemini · OC | ⬜ |
| K5 | Output styles | Switchable response styles (concise, explanatory, ...) | CC | ⬜ |

## L. Interface and user experience

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| L1 | Terminal REPL | Type a message, see the reply, repeat | all · SD | ⬜ |
| L2 | Rich terminal UI | Colors, panels, spinners, markdown rendering | DAI · BYO | ⬜ |
| L3 | Diff preview | Show the change before applying it | CC | ⬜ |
| L4 | Built-in slash commands | `/help`, `/clear`, `/model`, `/status` | CC · Codex · Gemini · Aider | ⬜ |
| L5 | Status line | Model, context %, tokens and cost always visible | CC | ⬜ |
| L6 | Notifications | Ping you when the agent is waiting for input | Aider · CC | ⬜ |
| L7 | Voice input | Speak instead of type | Aider · CC | ⬜ |
| L8 | Editor watch mode | Respond to special comments you write in your editor | Aider | ⬜ |
| L9 | Web UI | Run the agent in a browser | Aider | ⬜ |

## M. Automation and deployment

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| M1 | Headless mode | One-shot runs from scripts with JSON output (`-p`, `exec`) | CC · Gemini · Codex | ⬜ |
| M2 | Python library / SDK | Use the agent from your own code | CC · Aider · mini · OC | ⬜ |
| M3 | HTTP server | Expose the agent through an API | BYO · OC · OH | ⬜ |
| M4 | Chat integrations | Run it from Telegram or Slack | BYO · CC | ⬜ |
| M5 | GitHub integration | Turn issues into PRs; review PRs on `@mention` | CC · Gemini | ⬜ |
| M6 | Code review command | Review uncommitted changes or a branch without editing | Codex · CC | ⬜ |
| M7 | Scheduled runs | Cron-style triggers | CC · LCC · DAI | ⬜ |
| M8 | Cloud deployment | Run agents remotely in a sandboxed environment | BYO · DAI · Codex | ⬜ |

## N. Observability, cost and evaluation

| # | Component | What it is | Seen in | Status |
|---|---|---|---|---|
| N1 | Session log | Record every call and tool result; show tool calls on screen | SD · CC | ⬜ |
| N2 | Token and cost tracking | Count tokens and dollars per call and per session | CC | ⬜ |
| N3 | Tracing (OpenTelemetry) | Export traces and metrics to standard tools | CC · Gemini | ⬜ |
| N4 | Trajectory viewer | Browse a past run step by step | mini | ⬜ |
| N5 | Fake model for tests | Deterministic, free tests of the harness | SD | ⬜ |
| N6 | Benchmark tasks | A fixed set of tasks to score the agent | DAI · mini | ⬜ |
| N7 | Record and replay | Re-run a failed trajectory with a new prompt or model | DAI | ⬜ |
| N8 | Capstone task | A real end-to-end task the finished agent completes (e.g. a kata) | SD | ⬜ |

---

## How other "from scratch" projects are structured

| Project | Language | Steps | Structure | What stands out |
|---|---|---|---|---|
| [learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | Python | 17+ | One self-contained folder per session (`s01_agent_loop/` ...), each with `README.md` and a runnable `code.py` | **The loop never changes; each session adds exactly one mechanism around it.** Covers the widest range: permissions, hooks, skills, compaction, memory, tasks, cron, teams, MCP, workflows, goal loop |
| [decodingai course](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course) | Python | 8 lessons | One real package (`src/decode/`) with a module per concern; tests mirror `src/`; design decisions recorded in `docs/` | "Minimal agent, large harness": the loop is about 20 lines, everything else is harness. Strong on sandboxes, subagents and **evals** (benchmark plus record and replay) |
| [build-your-own-coding-agent](https://github.com/labdmitriy/build-your-own-coding-agent) | Python | 13 | `steps/01_first_api_call/` ... `13_cloud_deploy/`, each independently runnable | Goes past the terminal: HTTP server, Telegram, SQLite sessions, cloud deploy. Includes a self-extending "hot reload" tool step |
| [build-coding-agent-from-scratch](https://github.com/SDiamante13/build-coding-agent-from-scratch) | TypeScript | 10 | One growing `src/`, with an **acceptance test per lesson** run against a **fake model** | Ends with a capstone: the agent you built does a coding kata test-first |
| [how-to-build-a-coding-agent](https://github.com/ghuntley/how-to-build-a-coding-agent) | Go | 6 | One file per stage | Smallest path to a working coding agent: chat → read → list → bash → edit → search |
| [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | Python | (not a tutorial) | One ~100-line agent class | A counterpoint: **bash is the only tool**, and it still scores well on SWE-bench. Shows how far simplicity goes |

**Ideas worth borrowing for this repo:**

- **Keep the loop fixed; add one mechanism per step** (learn-claude-code). Makes each step easy to compare.
- **Self-contained step folders** (learn-claude-code, build-your-own-coding-agent). We already do this.
- **A fake model for tests** (build-coding-agent-from-scratch). Lets each step have a free, deterministic test.
- **A capstone task** (build-coding-agent-from-scratch). A real job the finished agent does end to end.
- **Write down the "why"** (decodingai). Short design notes on the decisions behind each step.
- **A "simplicity" counterpoint step** (mini-swe-agent). A bash-only agent shows what all the extra machinery buys you.

## Sources

Production agent docs:
- Claude Code: [docs index](https://code.claude.com/docs/llms.txt) · [How Claude Code works](https://code.claude.com/docs/en/how-claude-code-works) · [Tools reference](https://code.claude.com/docs/en/tools-reference)
- [Codex CLI](https://learn.chatgpt.com/docs/codex/cli)
- [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- Aider: [docs](https://aider.chat/docs/) · [repo map](https://aider.chat/docs/repomap.html)
- [OpenCode](https://opencode.ai/docs/)
- [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent)
- OpenHands: [overview](https://docs.openhands.dev/overview/introduction) · [SDK](https://docs.openhands.dev/sdk)

From-scratch projects: see the table above.
