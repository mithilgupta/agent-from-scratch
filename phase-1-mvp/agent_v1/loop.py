"""The system prompt, the tool-call parser, the approval prompt and the agent loop."""

import inspect
import json

from .llm import call_llm
from .tools import RISKY_TOOLS, TOOLS

VERIFY_INSTRUCTIONS = """When asked to fix a bug or a failing test, investigate with your tools instead of asking the user for details you can find yourself: run the tests to see what fails, then read the relevant code.
After changing code, run the tests again. If they still fail, read the output, fix, and run them again. Finish only when they pass, and say which command you ran and what it showed."""


def describe_tool(function) -> str:
    """One line for the prompt: name(parameters) - description."""
    params = ", ".join(inspect.signature(function).parameters)
    return f"  {function.__name__}({params}) - {function.__doc__}"


def example_call(function) -> str:
    """A real example of the tool-call line, with placeholder values."""
    args = {name: "..." for name in inspect.signature(function).parameters}
    return f"tool: {function.__name__}({json.dumps(args)})"


def build_system_prompt(tools: dict) -> str:
    tool_lines = "\n".join(describe_tool(f) for f in tools.values())
    first_tool = next(iter(tools.values()))
    return f"""You are a helpful coding assistant.

You have these tools:
{tool_lines}

To use a tool, reply with exactly one line and nothing else:
tool: tool_name({{"argument_name": "value"}})

For example:
{example_call(first_tool)}

After you receive a tool_result(...) message, use it to continue the task.
If you don't need a tool, just answer normally.

{VERIFY_INSTRUCTIONS}"""


class ToolFormatError(Exception):
    """The reply tried to call a tool, but the arguments couldn't be read."""


def parse_tool_call(reply: str):
    """Return (tool_name, args), None if there's no tool call, or raise ToolFormatError."""
    prefix = "tool: "
    for line in reply.splitlines():
        line = line.strip()
        if line.startswith(prefix) and line.endswith(")") and "(" in line:
            name, _, raw_args = line[len(prefix):-1].partition("(")
            try:
                args = json.loads(raw_args)
            except json.JSONDecodeError:
                raise ToolFormatError(f"The arguments are not valid JSON: {raw_args}")
            if not isinstance(args, dict):
                raise ToolFormatError(f'The arguments must be a JSON object, like {{"filename": "a.py"}}. Got: {raw_args}')
            return name, args
    return None


def run_tool(name: str, args: dict) -> dict:
    """Call a registered tool. Unknown tools and wrong arguments become error results."""
    if name not in TOOLS:
        return {"error": f"Unknown tool: {name}. Available tools: {', '.join(TOOLS)}"}

    function = TOOLS[name]
    try:
        inspect.signature(function).bind(**args)
    except TypeError:
        expected = ", ".join(inspect.signature(function).parameters)
        return {"error": f"Wrong arguments for {name}. Got: {', '.join(args) or 'none'}. Expected: {expected}"}

    return function(**args)


def approve(name: str) -> str | None:
    """Ask the user. Returns None if allowed, or the reason they gave for refusing."""
    answer = input(f"  Allow {name}? Press Enter to allow, or type why not: ").strip()
    return None if answer.lower() in ("", "y", "yes") else answer


def new_conversation() -> list:
    """A fresh conversation: just the system prompt."""
    return [{"role": "system", "content": build_system_prompt(TOOLS)}]


def ask(user_message: str, conversation: list, max_steps: int = 10) -> str:
    """Run the agent loop on one user message. Appends to `conversation`."""
    conversation.append({"role": "user", "content": user_message})

    for step in range(max_steps):
        reply = call_llm(conversation)                          # 1. ask the model
        conversation.append({"role": "assistant", "content": reply})

        try:
            call = parse_tool_call(reply)                       # 2. did it ask for a tool?
        except ToolFormatError as e:                            #    a broken call goes back to the model
            print(f"  [step {step + 1}] format error: {e}")
            conversation.append(
                {"role": "user", "content": f"tool_result({json.dumps({'error': str(e)})})"}
            )
            continue
        if call is None:
            print("Assistant:", reply)                          # 3a. no -> final answer
            return reply

        name, args = call
        print(f"  [step {step + 1}] model asked for {name}({args})")
        refusal = approve(name) if name in RISKY_TOOLS else None    # risky tools wait for the user's yes
        if refusal is None:
            result = run_tool(name, args)                       # 3b. yes -> run it
        else:
            result = {"error": f"The user refused this action. Their reason: {refusal}"}
        conversation.append(                                    # 4. send the result back
            {"role": "user", "content": f"tool_result({json.dumps(result)})"}
        )

    print("Stopped: too many tool calls.")
