"""The system prompt, the tool-call parser and the agent loop."""

import json

from .llm import call_llm
from .tools import read_file

SYSTEM_PROMPT = """You are a helpful coding assistant.

You have ONE tool:
  read_file(filename) - returns the contents of a text file.

To use it, reply with exactly one line and nothing else:
tool: read_file({"filename": "path/to/file"})

After you receive a tool_result(...) message, use it to continue the task.
If you don't need the tool, just answer normally."""


def parse_tool_call(reply: str):
    """Return the tool's arguments if the reply asks for read_file, else None."""
    prefix = "tool: read_file("
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith(prefix) and line.endswith(")"):
            try:
                return json.loads(line[len(prefix):-1])
            except json.JSONDecodeError:
                return None
    return None


def new_conversation() -> list:
    """A fresh conversation: just the system prompt."""
    return [{"role": "system", "content": SYSTEM_PROMPT}]


def ask(user_message: str, conversation: list, max_steps: int = 5) -> str:
    """Run the agent loop on one user message. Appends to `conversation`."""
    conversation.append({"role": "user", "content": user_message})

    for step in range(max_steps):
        reply = call_llm(conversation)                          # 1. ask the model
        conversation.append({"role": "assistant", "content": reply})

        args = parse_tool_call(reply)                           # 2. did it ask for a tool?
        if args is None:
            print("Assistant:", reply)                          # 3a. no -> final answer
            return reply

        print(f"  [step {step + 1}] model asked for read_file({args})")
        result = read_file(args.get("filename", ""))            # 3b. yes -> run the real function
        conversation.append(                                    # 4. send the result back
            {"role": "user", "content": f"tool_result({json.dumps(result)})"}
        )

    print("Stopped: too many tool calls.")
