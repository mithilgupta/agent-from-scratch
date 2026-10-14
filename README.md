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

## Steps

Each step is a self-contained folder with a notebook to run and a README that
explains it.

| # | Step | Status |
|---|---|---|
| 01 | [Minimal agent](01-minimal-agent/): one tool, the agent loop | ✅ |

What comes next is in [ROADMAP.md](ROADMAP.md): the plan, organized around
the problems every agent has to solve (control loop, tools, context, memory,
safety, orchestration, interfaces, evaluation) plus a track on the model
itself.

## Setup

Requires Python 3.10+.

```bash
pip install -r requirements.txt
cp .env.example .env    # then fill in your API key
jupyter lab             # open any step's agent.ipynb
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
