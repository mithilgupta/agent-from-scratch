# Roadmap

The idea: start with the smallest thing that can be called an agent, then add
one component at a time. Every step follows the same pattern:

1. **Break it.** Show a task the current agent can't handle.
2. **Fix it.** Add the one component that solves that problem.
3. **Explain it.** What the component is, and how production agents (Claude Code,
   Cursor, etc.) do the same thing at scale.

Each step folder is complete and runnable on its own; nothing imports from an
earlier step. Compare any two folders to see exactly what a component adds.

## Steps

| # | Step | Status | What breaks without it | What it adds | Related course week |
|---|---|---|---|---|---|
| 01 | [Minimal agent](01-minimal-agent/) | ✅ | (nothing yet: this is the baseline) | One tool (`read_file`), a text protocol for tool calls, and the agent loop | Week 1 |
| 02 | More tools | ⬜ | The agent can read a bug but can't fix it | `list_files` and `edit_file` | Week 1 |
| 03 | Tool registry | ⬜ | Hand-writing every tool into the prompt doesn't scale | Tools described automatically from their docstrings and signatures | Week 1 |
| 04 | Permissions | ⬜ | The agent can overwrite any file without asking | A "may I?" check before risky tools run | Week 4 |
| 05 | Context management | ⬜ | Long sessions get slow, expensive, and eventually overflow | Trim or summarize old conversation (short-term memory) | Week 2 |
| 06 | Native tool calling | ⬜ | Text parsing fails when the model formats a call slightly wrong | Structured tool calls through the API instead of parsing text | Week 2 |
| 07 | Long-term memory | ⬜ | Every new session starts from zero | Facts saved to a file and loaded into the system prompt at startup | Week 4 |
| 08 | Planning | ⬜ | Multi-step tasks drift or stop halfway | A to-do list tool the model writes and checks off | Week 1 |
| 09 | Subagents | ⬜ | Big side-tasks flood the main conversation with detail | Hand a sub-task to a fresh agent and keep only its summary | Week 4 |
| 10 | Observability | ⬜ | You can't see what it did, or what it cost | Log every call, token count, and cost | Week 9 |

"Course week" refers to the Fall 2026 syllabus of
[CS146S: The Modern Software Developer](https://themodernsoftware.dev/).

## Ideas parked for later

- Running shell commands (a `bash` tool) and the safety questions that come with it
- MCP: exposing the tools through the Model Context Protocol
- Skills: loading task-specific instructions only when relevant
- Evaluating the agent on a small fixed set of tasks
