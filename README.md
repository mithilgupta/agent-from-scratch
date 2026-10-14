# Agent from Scratch

Build a coding agent, the kind of thing behind Claude Code and Cursor, from
scratch in plain Python, **one component at a time**.

The surprising part: the core of a coding agent is about 60 lines. A language
model only ever turns text into text; everything an agent *does* (reading files,
editing code) is ordinary Python running in a loop around it. This repo starts
from that minimal loop and adds the pieces real agents need, step by step, with
an explanation of why each one exists.

## The core idea in one picture

```
You ──► conversation ──► LLM ──► reply
            ▲                      │
            │          does the reply ask for a tool?
            │             │                  │
            │            yes                 no ──► show the answer
            │             │
            └── tool result ◄── your Python runs the tool
```

## The plan

**[ROADMAP.md](ROADMAP.md) is the center of this project.** It explains how
agents work (organized around the problems every agent has to solve: control
loop, tools, context, memory, safety, orchestration, evaluation, interfaces,
plus a track on the model itself), and its **build order** says what gets
built next. Status is tracked there.

The repo is organized by the build order's phases, one folder each:

| Phase | Folder | Goal |
|---|---|---|
| 0 | [`phase-0-foundation/`](phase-0-foundation/) | The minimal agent: one tool, one loop |
| 1 | [`phase-1-mvp/`](phase-1-mvp/) | A coding agent that can fix a bug safely |
| 2 | [`phase-2-measure/`](phase-2-measure/) | Record what it does, what it costs, how well it scores |
| 3 | [`phase-3-robust/`](phase-3-robust/) | Structured tool calls and better context |
| 4 | [`phase-4-longer-tasks/`](phase-4-longer-tasks/) | Planning, compaction and long-term memory |
| 5 | [`phase-5-multi-agent/`](phase-5-multi-agent/) | Subagents and specialized agents |

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
cp .env.example .env    # then fill in your API key
jupyter lab             # open a phase's notebook, starting with phase-0-foundation/
```

**Works with any OpenAI-compatible provider.** Set three values in `.env`:

| Provider | `LLM_BASE_URL` | Example `LLM_MODEL` |
|---|---|---|
| [DeepInfra](https://deepinfra.com) (cheap open models) | `https://api.deepinfra.com/v1/openai` | `Qwen/Qwen3-Coder-480B-A35B-Instruct-Turbo` |
| [OpenAI](https://platform.openai.com) | `https://api.openai.com/v1` | an OpenAI chat model |
| [Ollama](https://ollama.com) (local, free) | `http://localhost:11434/v1` | `qwen3-coder` (or any model you've pulled) |

## Acknowledgements

Inspired by the "build a coding agent" lecture in Stanford's
[CS146S: The Modern Software Developer](https://themodernsoftware.dev/).
The code and explanations here are an independent, simplified re-implementation
for learning.
