# Phase 0: Foundation

The smallest thing that can be called an agent: **one tool, one loop**.
Open [`phase_0_agent.ipynb`](phase_0_agent.ipynb) and run it top to bottom.

Builds: agent loop, step limit, read file, system prompt, conversation history.
See [Phase 0 in the roadmap](../ROADMAP.md#phase-0-foundation).

## The one idea to take away

> **The LLM never does anything. It only produces text.**

The model is a function `f(conversation) → text`. It can't open files or run
code. What makes it an *agent* is ordinary Python around it:

1. We tell the model (in the system prompt) that if it wants a file, it should
   write a line in a special format: `tool: read_file({"filename": "..."})`.
2. Our code checks each reply for that line.
3. If it's there, **our code** reads the file and sends the contents back as the next message.
4. Repeat until the model replies without asking for a tool. That reply is the answer.

## The pieces

| Piece | What it is | Notes |
|---|---|---|
| `read_file()` | A plain Python function: the agent's only way to see anything | Returns a dict (easy to turn into text) and returns errors instead of crashing, so the model can react to them |
| `SYSTEM_PROMPT` | Instructions sent at the start of every conversation | The **only** way the model learns the tool exists. We're inventing a tiny text protocol. |
| `call_llm()` | Sends the whole conversation and returns the reply | The "predict" step. The model sits behind an API, not in your Python process. |
| `parse_tool_call()` | Looks for `tool: read_file({...})` in a reply | Turns free text into structured data: a dict of arguments, or `None` |
| `ask()` | The agent loop | Call model → tool requested? → run it → send the result back → repeat |

## Walkthrough: one question, start to finish

Asking `"What will sandbox/hello.py print when I run it?"` grows the
`conversation` list like this:

| # | Role | Content | Written by |
|---|---|---|---|
| 0 | system | "You are a helpful coding assistant... you have ONE tool..." | us (the prompt) |
| 1 | user | "What will sandbox/hello.py print when I run it?" | you |
| 2 | assistant | `tool: read_file({"filename": "sandbox/hello.py"})` | the model, *asking* |
| 3 | user | `tool_result({"filename": ..., "content": ...})` | **our Python code** |
| 4 | assistant | "It will print `hello world`..." | the model, now with the file |

Message 3 is the key: the tool result goes back as a **user** message. The
model only reads text, so our code talks to it on the user's behalf.

## Memory, for free

The model has no memory; every API call starts from scratch. That's why
`call_llm()` sends the **entire** `conversation` every time. Because
`conversation` lives outside `ask()`, follow-up questions work:

```python
ask("What's in sandbox/hello.py?")
ask("If I changed the name to Alex, what would it print?")   # knows which file
```

The `conversation` list *is* the agent's memory. Every memory feature in real
LLM apps (chat history, summaries, saved notes, retrieval) comes down to
deciding what text goes into that list.

## Limitations (what later phases fix)

- It can only **read**, so it can explain a bug but not fix it → Phase 1 (write and edit files)
- The tool is described **by hand** in the prompt → Phase 1 (tool registry)
- The tool call is found by **parsing text**; a slightly different format is silently missed → Phase 3 (native tool calling)
- `conversation` grows forever → Phase 4 (compaction)

## Prod code: `agent_v0`

Once the notebook was done, its code was moved into a package,
[`agent_v0/`](agent_v0/), so Phase 1 can import it (see
[WORKFLOW.md](../WORKFLOW.md)). It's **frozen**: later phases never change it.

| File | Holds |
|---|---|
| `llm.py` | `get_client()`, `call_llm()` |
| `tools.py` | `read_file()` |
| `loop.py` | `SYSTEM_PROMPT`, `parse_tool_call()`, `new_conversation()`, `ask()` |
| `tests/` | Offline tests; none of them call the model |

The code is the notebook's, with two changes to make it importable:

- **The client connects on first use** (`get_client()`), not at import, so
  importing the package doesn't need a `.env`.
- **No global `conversation`.** `ask(message, conversation)` takes the list
  explicitly, and `new_conversation()` makes a fresh one:

```python
import sys; sys.path.insert(0, "../phase-0-foundation")
from agent_v0 import ask, new_conversation

conversation = new_conversation()
ask("What will sandbox/hello.py print when I run it?", conversation)
```

Run the tests with `pytest phase-0-foundation/agent_v0` from the repo root.

## Try it

Predict what happens before you run each one:

1. `ask("What's the capital of France?")`: does it use the tool?
2. `ask("What does sandbox/missing.py contain?")`: what does the model see?
3. After a few questions, print `conversation`. Can you match each message to the table above?
4. Run `conversation = conversation[:1]` (keep only the system prompt), then ask a follow-up question. Watch it forget.
