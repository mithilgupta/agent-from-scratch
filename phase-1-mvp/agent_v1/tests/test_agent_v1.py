"""Offline tests: nothing here calls the model."""

import builtins
from pathlib import Path

import pytest

import agent_v1.loop as loop
import agent_v1.tools as tools
from agent_v1 import (TOOLS, ToolFormatError, ask, build_system_prompt, edit_file, find_files, new_conversation,
                      parse_tool_call, read_file, run_command, run_tool, set_project_root)


@pytest.fixture
def project(tmp_path):
    """A small project folder for the agent, restored afterwards."""
    old_root = tools.ROOT
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "config.json").write_text('{"debug": false}\n')
    (tmp_path / "hello.py").write_text('print("hello")\n')
    set_project_root(tmp_path)
    yield tmp_path
    tools.ROOT = old_root


def scripted_model(monkeypatch, replies):
    """Replace the model with a fixed list of replies."""
    replies = iter(replies)
    monkeypatch.setattr(loop, "call_llm", lambda conversation: next(replies))


def keyboard(monkeypatch, answers):
    """Replace the keyboard with a fixed list of answers to the approval prompt."""
    answers = iter(answers)
    monkeypatch.setattr(builtins, "input", lambda prompt: next(answers))


# The registry and the prompt

def test_every_tool_is_registered_and_in_the_prompt():
    assert set(TOOLS) == {"read_file", "find_files", "edit_file", "run_command"}
    prompt = build_system_prompt(TOOLS)
    for name in TOOLS:
        assert f"  {name}(" in prompt


def test_prompt_asks_the_model_to_investigate_and_verify():
    prompt = new_conversation()[0]["content"]
    assert "investigate with your tools" in prompt
    assert "Finish only when they pass" in prompt


# The parser: three outcomes

def test_parse_finds_a_tool_call_after_other_text():
    reply = 'Let me look.\ntool: read_file({"filename": "a.py"})'
    assert parse_tool_call(reply) == ("read_file", {"filename": "a.py"})


def test_parse_returns_none_for_a_normal_answer():
    assert parse_tool_call("It prints hello.") is None


def test_parse_raises_on_broken_arguments():
    with pytest.raises(ToolFormatError):
        parse_tool_call('tool: read_file({filename: "a.py"})')
    with pytest.raises(ToolFormatError):
        parse_tool_call('tool: read_file("a.py")')


# run_tool

def test_run_tool_turns_mistakes_into_error_results(project):
    assert "Unknown tool" in run_tool("delete_everything", {})["error"]
    assert "Wrong arguments" in run_tool("read_file", {"path": "hello.py"})["error"]


# The folder boundary

def test_read_file_reads_inside_the_project(project):
    assert read_file("hello.py") == {"filename": "hello.py", "content": 'print("hello")\n'}


@pytest.mark.parametrize("path", ["../outside.txt", "/etc/hosts"])
def test_read_file_refuses_paths_outside(project, path):
    assert "outside the project folder" in read_file(path)["error"]


def test_symlinks_pointing_outside_are_refused(project, tmp_path_factory):
    outside = tmp_path_factory.mktemp("outside")
    (outside / "secret.txt").write_text("secret")
    (project / "link").symlink_to(outside)
    assert "outside the project folder" in read_file("link/secret.txt")["error"]
    assert find_files("link/*")["files"] == []


def test_find_files_finds_by_name_relative_to_the_project(project):
    assert find_files("**/*.json") == {"files": ["app/config.json"]}
    assert find_files("../*")["files"] == []


def test_find_files_caps_results(project):
    for i in range(15):
        (project / f"f{i:02}.txt").write_text("")
    result = find_files("*.txt")
    assert len(result["files"]) == tools.MAX_RESULTS
    assert "Narrow your pattern" in result["note"]


# The edit tool

def test_edit_file_replaces_text(project):
    assert edit_file("hello.py", '"hello"', '"hi"') == {"result": "Edited hello.py."}
    assert (project / "hello.py").read_text() == 'print("hi")\n'


def test_edit_file_refuses_missing_repeated_and_outside_text(project):
    (project / "twice.py").write_text("x = 1\nx = 1\n")
    assert "not found" in edit_file("hello.py", "nope", "x")["error"]
    assert "appears 2 times" in edit_file("twice.py", "x = 1", "x = 2")["error"]
    assert "outside the project folder" in edit_file("../x.py", "a", "b")["error"]
    assert (project / "twice.py").read_text() == "x = 1\nx = 1\n"


# The shell tool

def test_run_command_returns_exit_code_and_output(project):
    assert run_command("echo hi") == {"exit_code": 0, "output": "hi\n"}
    assert run_command("ls no_such_file")["exit_code"] != 0


def test_run_command_runs_in_the_project_folder(project):
    assert run_command("ls")["output"].split() == ["app", "hello.py"]


def test_run_command_stops_at_the_time_limit(project, monkeypatch):
    monkeypatch.setattr(tools, "COMMAND_TIMEOUT", 1)
    assert "took longer than 1 seconds" in run_command("sleep 3")["error"]


# The approval prompt and the loop

def test_reading_never_asks_and_an_approved_edit_runs(project, monkeypatch):
    scripted_model(monkeypatch, [
        'tool: read_file({"filename": "hello.py"})',
        'tool: edit_file({"filename": "hello.py", "old_text": "\\"hello\\"", "new_text": "\\"hi\\""})',
        "Done.",
    ])
    keyboard(monkeypatch, [""])                     # one answer only: the read must not ask
    assert ask("Change hello to hi.", new_conversation()) == "Done."
    assert (project / "hello.py").read_text() == 'print("hi")\n'


def test_a_refused_edit_does_not_run_and_the_model_gets_the_reason(project, monkeypatch):
    scripted_model(monkeypatch, [
        'tool: edit_file({"filename": "hello.py", "old_text": "\\"hello\\"", "new_text": "\\"hi\\""})',
        "OK, I won't.",
    ])
    keyboard(monkeypatch, ["too risky"])
    conversation = new_conversation()
    ask("Change hello to hi.", conversation)
    assert (project / "hello.py").read_text() == 'print("hello")\n'
    assert "The user refused this action. Their reason: too risky" in conversation[-2]["content"]


def test_a_broken_tool_call_goes_back_to_the_model(project, monkeypatch):
    scripted_model(monkeypatch, ['tool: read_file({filename: "hello.py"})', "Sorry."])
    conversation = new_conversation()
    ask("Read hello.py", conversation)
    assert "not valid JSON" in conversation[3]["content"]


def test_the_step_limit_stops_a_model_that_never_finishes(project, monkeypatch):
    scripted_model(monkeypatch, ['tool: find_files({"pattern": "*"})'] * 20)
    assert ask("Look around.", new_conversation(), max_steps=3) is None
