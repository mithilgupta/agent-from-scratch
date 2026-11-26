"""The agent's tools, the registry that lists them, and the folder they work in."""

import os
import subprocess
import sys
from pathlib import Path

# The registry: tool name -> Python function. The prompt and the loop read from it.
TOOLS = {}

# Tools that change something: the loop asks the user before running them.
RISKY_TOOLS = {"edit_file", "run_command"}

# The folder boundary: file tools can't reach outside it, and commands run in it.
ROOT = Path.cwd().resolve()

MAX_RESULTS = 10
COMMAND_TIMEOUT = 30
MAX_OUTPUT = 10_000


def register(function):
    """Make a Python function available to the model as a tool."""
    TOOLS[function.__name__] = function
    return function


def set_project_root(path) -> Path:
    """Point the agent at a project folder. By default it's the folder Python started in."""
    global ROOT
    ROOT = Path(path).resolve()
    return ROOT


def inside_project(path) -> bool:
    """True if the path, with symlinks followed, ends up inside ROOT."""
    return (ROOT / path).resolve().is_relative_to(ROOT)


@register
def read_file(filename: str) -> dict:
    """Read a text file and return its contents."""
    if not inside_project(filename):
        return {"error": f"{filename} is outside the project folder. Only files inside it can be read, with paths relative to it."}
    path = ROOT / filename
    if not path.exists():
        return {"error": f"File not found: {filename}"}
    return {"filename": filename, "content": path.read_text()}


@register
def find_files(pattern: str) -> dict:
    """Find files by name with a glob pattern, e.g. "*.py" or "**/*.json". Patterns only search the top folder; use **/ to search subfolders."""
    matches = sorted(
        str(path.relative_to(ROOT)) for path in ROOT.glob(pattern)
        if path.is_file() and inside_project(path)
        and not any(part.startswith(".") for part in path.relative_to(ROOT).parts)
    )
    if not matches:
        return {"files": [], "note": "No files match. Use **/ to search subfolders."}
    if len(matches) > MAX_RESULTS:
        return {"files": matches[:MAX_RESULTS],
                "note": f"Showing {MAX_RESULTS} of {len(matches)} files. Narrow your pattern."}
    return {"files": matches}


@register
def edit_file(filename: str, old_text: str, new_text: str) -> dict:
    """Replace old_text with new_text in a file. Read the file first: old_text must be copied exactly (spaces included) and appear once."""
    if not inside_project(filename):
        return {"error": f"{filename} is outside the project folder. Only files inside it can be edited, with paths relative to it."}
    path = ROOT / filename
    if not path.exists():
        return {"error": f"File not found: {filename}"}
    text = path.read_text()
    count = text.count(old_text)
    if count == 0:
        return {"error": f"old_text was not found in {filename}. Read the file and copy the text exactly, including spaces."}
    if count > 1:
        return {"error": f"old_text appears {count} times in {filename}. Include more of the surrounding code so it appears once."}
    path.write_text(text.replace(old_text, new_text))
    return {"result": f"Edited {filename}."}


@register
def run_command(command: str) -> dict:
    """Run a shell command in the project folder and return its exit code and output. Use it to run tests, e.g. "python -m pytest"."""
    env = os.environ | {"PATH": os.path.dirname(sys.executable) + os.pathsep + os.environ["PATH"]}   # this Python first
    try:
        r = subprocess.run(command, shell=True, cwd=ROOT, env=env, timeout=COMMAND_TIMEOUT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    except subprocess.TimeoutExpired:
        return {"error": f"The command took longer than {COMMAND_TIMEOUT} seconds and was stopped."}
    output = r.stdout
    if len(output) > MAX_OUTPUT:                                        # keep the start and the end
        half = MAX_OUTPUT // 2
        output = output[:half] + f"\n... ({len(output) - MAX_OUTPUT} characters cut) ...\n" + output[-half:]
    return {"exit_code": r.returncode, "output": output}
