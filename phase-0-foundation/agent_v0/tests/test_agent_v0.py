"""Offline tests: nothing here calls the model."""

from agent_v0 import SYSTEM_PROMPT, new_conversation, parse_tool_call, read_file


# read_file

def test_read_file_returns_contents(tmp_path):
    f = tmp_path / "hello.py"
    f.write_text('print("hi")\n')
    assert read_file(str(f)) == {"filename": str(f), "content": 'print("hi")\n'}


def test_read_file_missing_returns_error_instead_of_crashing(tmp_path):
    missing = str(tmp_path / "nope.txt")
    assert read_file(missing) == {"error": f"File not found: {missing}"}


# parse_tool_call

def test_parse_finds_tool_call():
    reply = 'tool: read_file({"filename": "sandbox/hello.py"})'
    assert parse_tool_call(reply) == {"filename": "sandbox/hello.py"}


def test_parse_finds_tool_call_after_other_text():
    # Seen live: the model often writes a sentence before the tool line.
    reply = 'I\'ll check the file.\n\ntool: read_file({"filename": "a.py"})'
    assert parse_tool_call(reply) == {"filename": "a.py"}


def test_parse_ignores_plain_answer():
    assert parse_tool_call("The answer is 4.") is None


def test_parse_bad_json_returns_none():
    assert parse_tool_call("tool: read_file({filename: a.py})") is None


def test_parse_misses_slightly_different_format():
    # The fragility the README warns about: no space after "tool:" is missed.
    assert parse_tool_call('tool:read_file({"filename": "a.py"})') is None


# conversation

def test_new_conversation_starts_with_system_prompt_only():
    assert new_conversation() == [{"role": "system", "content": SYSTEM_PROMPT}]


def test_new_conversations_are_independent():
    a = new_conversation()
    a.append({"role": "user", "content": "hi"})
    assert len(new_conversation()) == 1
