"""The agent's only tool."""

from pathlib import Path


def read_file(filename: str) -> dict:
    """Read a text file and return its contents."""
    path = Path(filename)
    if not path.exists():
        return {"error": f"File not found: {filename}"}
    return {"filename": filename, "content": path.read_text()}
