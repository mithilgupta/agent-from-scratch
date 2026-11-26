# Phase 1 research

The full game plan of each Phase 1 step: the problem broken down, how real agents do it (read from their source code, with links pinned to the commit read), the options and what was dropped as too complex, and the coverage check. The notebook ([phase_1_agent.ipynb](phase_1_agent.ipynb)) keeps a short summary of each step and links here.

Steps 1 (tool registry) and 2 (list and find files) are not here: their plans are still in the notebook, where they were written before this file existed.

## Step 3: Folder boundary

*Agreed 2026-11-24: decision A refuse, decision B the `sandbox/` folder. One sub-step.*

### 1. What we're doing and why

**The goal in one sentence:** limit the files the agent can read or change to one project folder.

Today there's no limit. Our agent has two tools that touch files, and both reach anywhere on the machine:

- `read_file`, the reading tool from Phase 0's frozen code ([`agent_v0/tools.py:6-11`](../phase-0-foundation/agent_v0/tools.py)), opens whatever path the model sends. A probe on 2026-11-24 confirmed it can read `/etc/hosts`, and so it could read `~/.ssh/...` or another project's `.env` secrets.
- `find_files`, the file-search tool built in section 2 of this notebook, has no boundary either. `../` patterns happen to return nothing, **but only by accident**: its filter for hidden names (those starting with `.`) also matches `..`. A shortcut (symlink) inside the project that points outside still gets through: on 2026-11-24 a test symlink in `sandbox/` pointing at `phase-0-foundation/` listed that folder's files. (An earlier draft of this plan said `find_files("../*")` listed 23 entries; that count came from a bare `Path.glob`, not from `find_files`.)

The roadmap puts this before the agent can write files ([`ROADMAP.md:72`](../ROADMAP.md)): *"Keep file tools inside the project before any of them can write."*

**The problem broken down (MECE).**

*By action:* the agent can do two things to a file.

| Action | Our tools that do it | Live today? | What goes wrong without a boundary |
|---|---|---|---|
| **Read** (including listing and searching) | `read_file`, `find_files` | ✅ | Privacy: it can read secrets anywhere |
| **Write** (create, edit, delete) | None yet: the file-edit tool is the next roadmap step | ❌ | Damage: it could break files anywhere |

*By channel:* the agent can reach a file in two ways.

| Channel | Live today? |
|---|---|
| **Our own file tools** (Python functions we write and register) | ✅ |
| **Terminal commands** (e.g. `cat secret.txt`), through a command tool planned later in Phase 1 to run the tests | ❌ |

So the only live part of the problem today is **reading, through our own file tools**. Writing through our tools arrives with the file-edit tool; anything through terminal commands arrives with the command tool.

### 2. Evidence: how real agents do it


Source code read on 2026-11-24 from local clones, links pinned to the commit read. **This is a snapshot:** these repos change daily, so the tables describe them as of that date and aren't updated afterwards.

**By question: what they agree on, where they differ, and what we follow** (the sources are in the per-agent table below):

| Question | What real agents do | For us |
|---|---|---|
| Do the file tools have a boundary? | **Most do:** learn-claude-code, Gemini CLI, opencode, Codex (writes only), Aider (edits), Claude Code (docs). **Two have none in the tool:** ghuntley (reads any path) and OpenHands' default file editor, which wants absolute paths and relies on running inside a **Docker container** instead. mini-swe-agent has no file tools; its isolation is also the container. | A check in our tools: we run on the Mac directly, with no container. |
| Outside the boundary: refuse or ask? | **Refuse:** learn-claude-code, Gemini CLI. **Ask the user:** opencode (an `external_directory` permission, *ask* by default), Claude Code (docs), Aider (edits), Codex (writes; refuses when approvals are off). | They differ: your call, decision A below |
| Reads too, or only writes? | **Both:** learn-claude-code, Gemini CLI, opencode, Claude Code. **Writes only:** Codex reads the **entire disk** by design (*"can read the entire disk, but can only write to the current working directory"*). | Settled by our breakdown: both (see section 3) |
| How is "inside" checked? | **Turn the path into a full absolute path, then check it's under the root folder.** learn-claude-code: `(WORKDIR / p).resolve()` then `is_relative_to(WORKDIR)`. Gemini CLI: the same, and it also **follows symlinks** (shortcuts to other files) to their real target first. opencode compares the paths as text only, without following symlinks. | **Follow learn-claude-code:** two lines of Python. Python's `Path.resolve()` follows symlinks too, so a shortcut inside the project pointing outside it is caught (we'll test that). |
| Where is the root folder? | **The folder the agent started in:** learn-claude-code (`Path.cwd()`), Codex (current folder), opencode (the folder plus its project), Claude Code (*"the folder where it was started"*). Gemini CLI: the starting folder plus any extra folders the user lists with `--include-directories`. | They agree on the starting folder, but which folder that is for us is your call: decision B below |
| What does the model get back? | **An error that says where it may go:** Gemini CLI: *"Path not in workspace: ... resolves outside the allowed workspace directories: ..."*; learn-claude-code: *"Path escapes workspace"*. | An error result naming the allowed folder, like Gemini CLI, so the model knows what to try instead. It's returned as `{"error": ...}`, the same way our tool runner (`run_tool`, from section 1) already reports unknown tools. |
| Are search results filtered too? | **Yes:** learn-claude-code drops search matches outside the workspace; Gemini CLI runs every search result through the same check. | `find_files` drops matches outside the root. |

**One agent at a time** (the record behind the table above):

| Tier | Agent | Boundary on file tools | Source |
|---|---|---|---|
| Small scale | **learn-claude-code** | `safe_path()`: join the path to `WORKDIR` (the folder it started in), resolve it, and raise *"Path escapes workspace"* unless it's under `WORKDIR`. Used by read, write and edit; search results get the same filter. **Refuses**, reads included. | [`s02_tool_use/code.py:44, 81-85, 120-127`](https://github.com/shareAI-lab/learn-claude-code/blob/7226f555d48900076eba126acf37c9ed5f002b5d/s02_tool_use/code.py#L81-L85) |
| Small scale | **ghuntley** | **None:** `read_file` calls `os.ReadFile(path)` on whatever path it gets. | [`read.go:273-288`](https://github.com/ghuntley/how-to-build-a-coding-agent/blob/fa3dd49fdddf45e92b35c66746e6bb6aac6ac27e/read.go#L273-L288) |
| Small scale | **mini-swe-agent** | **No file tools, no path check:** its one tool runs shell commands in a folder, either directly on the machine or inside a Docker container (`DockerEnvironment`); the container is the boundary. | [`environments/local.py:24-29`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py#L24-L29); [`environments/docker.py:45`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/docker.py#L45) |
| Industry | **Gemini CLI** | Every file tool calls `validatePathAccess` (for a read or a write). The path is resolved **following symlinks**, then checked against the workspace folders (the starting folder plus `--include-directories`). **Refuses**, with an error naming the allowed folders. Even inside, it rejects path parts like `.git`, `.env` and `node_modules`. Search results go through the same check. | [`workspaceContext.ts:184-201, 236-256`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/utils/workspaceContext.ts#L184-L256); [`config.ts:3400-3459`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/config/config.ts#L3400-L3459); [`read-file.ts:135-154`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/read-file.ts#L135-L154); [`glob.ts:241-244`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/glob.ts#L241-L244); [`paths.ts:769-781`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/utils/paths.ts#L769-L781) |
| Industry | **Codex CLI** | **Reads: no boundary.** The default policy *"can read the entire disk, but can only write to the current working directory and the per-user tmp dir"*. A patch (Codex's way of editing files) that writes outside those folders **asks** the user, or is **rejected** (*"writing outside of the project"*) when approvals are turned off. macOS's built-in sandbox (Seatbelt) enforces the same rule again on every command. Inside the project, `.git` stays read-only. | [`protocol.rs:1410-1424`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/protocol/src/protocol.rs#L1410-L1424); [`safety.rs:13-16, 100-123, 146-180`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/core/src/safety.rs#L100-L123); [`permissions.rs:2376-2396`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/protocol/src/permissions.rs#L2376-L2396) |
| Industry | **opencode** | Each path is turned into a full path (as text, without following symlinks) and counted as inside if it's under the folder or its project. A path outside triggers an `external_directory` permission check before the read or write. With no rule configured, a permission check **asks** the user. | [`file-access.ts:95-141`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/file-access.ts#L95-L141); [`permission.ts:86-95`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/permission.ts#L86-L95) |
| Industry | **OpenHands** | **No boundary in the default file editor:** it requires an absolute path and checks only that it exists; its `workspace_root` setting is used just to suggest paths. The default setup runs the agent in a **Docker container** (`DockerWorkspace`), which is the boundary. Its separate patch tool, `apply_patch` (not in the default tool set), does refuse *"Absolute or escaping paths"*. | [`file_editor/editor.py:657-694`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/file_editor/editor.py#L657-L694); [`preset/default.py:51-57`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/preset/default.py#L51-L57); [`apply_patch/definition.py:74-83`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/apply_patch/definition.py#L74-L83); [`docker/workspace.py:53-58`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-workspace/openhands/workspace/docker/workspace.py#L53-L58) |
| Industry | **Aider** | **The user, not the model, chooses the files:** there's no read tool, and the user's `/add` command refuses files *"not part of the repository"*. An edit to a file the user didn't add **asks**: *"Allow edits to file that has not been added to the chat?"* | [`base_coder.py:2191-2238`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2191-L2238); [`commands.py:869-883`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L869-L883) |
| Closed (docs) | **Claude Code** | *"In Manual mode, Claude Code asks you before its file tools read or write outside the folder where it was started and its subfolders. The boundary is a permission prompt, so a Bash command you approve can still write anywhere your user account can."* **Asks**, reads included. | [Security docs, "Built-in protections"](https://code.claude.com/docs/en/security) (public docs, read 2026-11-24) |


**What they agree on → what we follow:** the boundary is **the folder the agent works in**, checked by **turning the path into a full path and testing that it's under that folder**, applied to **every file tool, search results included**.

**Where they differ:** refuse or ask (agents that already have a way to ask the user ask; the simplest ones refuse), and who enforces the boundary (section 3 below).

**Cross-check with a survey.** The *Harness Engineering* survey ([Barbaste et al., July 2026](https://arxiv.org/abs/2609.00006)) matches what we read: its table of sandboxing mechanisms (Table 8, p.30) lists opencode as *"policy-only"* (rules in code, no operating-system wall) and Aider as *"None (direct local execution)"*, and notes Codex keeps `.git` read-only inside writable folders (p.31).

### 3. Sub-steps and decisions, derived top-down

**The options the research gives**, grouped by who enforces the boundary:

| Option | Who does it | How |
|---|---|---|
| **A. No boundary** | ghuntley; OpenHands' file editor on its own | The tools open any path |
| **B. A wall built by the operating system** | OpenHands and mini-swe-agent (Docker containers); Codex (macOS's built-in sandbox) | The agent runs where everything outside the project is invisible or locked, whatever tool or command it uses |
| **C. A check inside our tool code** | learn-claude-code, Gemini CLI, opencode, Codex (for its edits), Aider (for its edits) | Each file tool checks the path before touching the file |

**Filter by this project's level of complexity:**

- **A (no boundary): dropped.** It doesn't meet the goal.
- **B (operating-system wall): dropped.** Containers and OS sandboxes are out of scope for this project (the user's call, 2026-11-24). The cost: once the agent can run terminal commands, a command like `cat` gets around option C. There, the user's yes/no before each command will be the only guard. We state that as a known limitation rather than fix it.
- **C (a check in our code): what's left.** A few lines of Python, and the rule is readable right in the notebook.

**Within option C, the choices the agents make:**

| Choice | What the agents do | Result |
|---|---|---|
| How to check a path | All agree: turn it into a full path (Python's `resolve()`, which also follows symlinks), then test it's under the project folder. learn-claude-code does it in two lines. | **Settled:** copy learn-claude-code. |
| What the model gets back | All agree: an error saying the path is outside. Gemini CLI also names the allowed folder. | **Settled:** an `{"error": ...}` result naming the allowed folder, so the model knows where it can look. |
| Bound reads too, or only writes? | Most bound both; Codex bounds only writes. | **Settled by our breakdown:** writing doesn't exist yet, so a writes-only boundary would do nothing now. Reads are bounded now; the file-edit tool will call the same check. |
| Protect files *inside* the project (`.git`, `.env`) | Only Codex and Gemini CLI | **Dropped:** beyond our level. |
| Refuse, or ask the user? | They split: learn-claude-code and Gemini CLI refuse; opencode, Claude Code and Aider ask. Asking needs an approval prompt, which we don't have yet. | **Decision A** |
| Which folder is the boundary? | All use the folder the agent started in. For us: the notebook's folder or the `sandbox/` project inside it. | **Decision B** |

**Decisions (agreed 2026-11-24, both as Claude leaned):**

- **Decision A: outside the folder, refuse or ask?** My lean: **refuse.** Asking needs an approval prompt (the user sees each risky action and says yes or no), which is a later roadmap step. When it's built, this refusal is the natural place to switch to asking, as opencode and Claude Code do. -- Agreed.
- **Decision B: which folder is the boundary?**
  - **(a) The notebook's folder, `phase-1-mvp/`:** no path changes (the model keeps using `sandbox/hello.py`), but the agent can reach this notebook, and once it can write, edit it.
  - **(b) `phase-1-mvp/sandbox/`**, the small project the agent works on: paths become relative to it (`hello.py`, not `sandbox/hello.py`), so the tools join paths to that folder before checking, as learn-claude-code does. The agent can't touch its own code.

  My lean: **(b).** Claude's judgment, not from a source: it matches Phase 1's goal (*"given a small project with a failing test, the agent finds the bug, fixes it..."*) and keeps the agent's future writes away from the notebook. -- Agreed. B is fine. we leave the notebooks and scripts folders as is and create a sandbox folder for all "experiments". we can follow this pattern for later phases as well.

**Sub-steps:**

One sub-step, because there's one feature: the check. Running it against the model is how we test that feature, not a separate piece of work, so it lives in the same cell.

| # | Sub-step | Based on |
|---|---|---|
| 3a | **Build the check, and test it.** One helper that tests a path, `inside_project(path)`, used by `read_file` (Phase 0's version plus the check) and `find_files` (section 2's version plus a filter that drops matches outside the folder). Test it without the model, through `run_tool` (the function the agent loop uses to call tools): a normal path, a `../` path, `/etc/hosts`, a `../*` search, and a symlink inside the project that points outside it. Then ask the agent for a file outside the project and record what the model does with the refusal: try another path, give up, or explain to the user (the finding about agent behavior; the choice of question is Claude's judgment). | Option C; learn-claude-code's `safe_path`; the "settled" rows above |

### 4. Coverage check: the breakdown against the sub-steps

| Part of the problem | Live today? | Covered by |
|---|---|---|
| Reading, through our file tools | ✅ | **3a** builds the check into `read_file` and `find_files`, and tests it offline and with the model |
| Writing, through our file tools | ❌ | **Deferred** to the file-edit step: the new tool calls the same `inside_project` check. Noted here so that step's plan includes it. |
| Reading or writing, through terminal commands | ❌ | **Dropped from the boundary:** that needs an operating-system wall (option B), which is out of scope. Guarded instead by the user's yes/no before each command, in the approval-prompt step. A known limitation. |

### 5. Done when

- `read_file` refuses a path outside the folder (a `../` path, an absolute path, a symlink pointing out) with an error naming the allowed folder, and still reads paths inside it.
- `find_files` never returns a path outside the folder, including through a symlink, and no longer relies on the hidden-name filter to block `../`.
- Asked for a file outside the project, the agent gets the refusal and doesn't read the file; we record what the model does next.

---

## Step 4: Write and edit files

*Agreed 2026-11-26: decision A find-and-replace, decision B no create/overwrite tool for now.*

### 1. What we're doing and why

**The goal in one sentence:** let the agent change a file inside the project, which is the "fixes it" part of Phase 1's goal (*"given a small project with a failing test, the agent finds the bug, fixes it, runs the tests..."*).

Today it can't. Its only tools are `read_file` and `find_files` (both now limited to the `sandbox/` folder by the folder boundary built in step 3). It can explain a fix, but not make one. The roadmap ([`ROADMAP.md:73`](../ROADMAP.md)): *"The moment the agent can actually change code."*

**The problem broken down (MECE).**

*By what the agent does to a file:*

| Action | Needed for the Phase 1 goal? |
|---|---|
| **Change part of an existing file** (fix one line) | ✅ This is the fix itself |
| **Create a new file** | ❌ Not for fixing a bug; maybe later (e.g. writing a new test) |
| **Rewrite a whole existing file** | Only as one *way* of changing part of it (see the options in section 3) |
| **Delete or rename a file** | ❌ |

*By what can go wrong when the model edits:*

| Risk | Who guards it |
|---|---|
| The text the model wants to replace **isn't in the file** (it misremembered a line, or got whitespace wrong) | This step: the edit tool must notice and say so |
| The text appears **more than once**, so the tool doesn't know which one to change | This step |
| The model edits a file **outside the project** | Already built: the folder check `inside_project` from step 3; the new tool must call it |
| The model makes a change **you didn't want** | Not this step: the approval prompt, a later roadmap step where you say yes or no before each risky action |

So this step is: **one way to change part of an existing file, safely refusing when the text is missing, ambiguous, or outside the folder.**

### 2. Evidence: how real agents do it

Source code read on 2026-11-24 from local clones, links pinned to the commit read. **This is a snapshot:** these repos change daily, so the tables describe them as of that date and aren't updated afterwards.

**By question:**

| Question | What real agents do |
|---|---|
| What does the model send to change a file? | **Find-and-replace** (the exact old text, plus the new text) is the most common: learn-claude-code, ghuntley, Gemini CLI, opencode (most models), OpenHands, Claude Code (docs). **A patch** in a custom diff-like format: Codex, and opencode for GPT models. **The whole new file:** Aider's default for models it doesn't know. **Shell commands** (`sed`): mini-swe-agent. |
| A separate tool to create or overwrite whole files? | **Usually yes,** next to the edit tool: learn-claude-code, Gemini CLI, opencode, Claude Code (`Write`). OpenHands can create but refuses to overwrite. ghuntley folds creating into its edit tool (empty old text + missing file = create). |
| Must the old text appear exactly once? | **Yes, almost everywhere:** ghuntley, Gemini CLI, opencode, OpenHands, Claude Code, each failing on several matches unless the model sets a "replace all" flag. **Only learn-claude-code** silently replaces the first match. |
| What if the old text doesn't match exactly? | **Error only:** learn-claude-code, ghuntley, Claude Code (*"doesn't use regex or fuzzy matching"*). **One retry, stripping outer whitespace:** OpenHands. **A cascade of looser matches:** Codex (ignore trailing spaces, then all outer spaces, then fancy punctuation), opencode (fancy quotes and dashes, then trailing spaces), Gemini CLI (flexible whitespace, then regex, then fuzzy, then **asks a second model to repair the edit**). |
| What does the model get back on failure? | **An error that says which failure and what to do:** "not found" vs "found N times" are separate messages in Gemini CLI, opencode and OpenHands. OpenHands lists the line numbers of the duplicates; opencode shows the closest lines it found; Gemini CLI says to re-read the file before retrying. |
| Does the format depend on the model? | **Yes, in two agents:** opencode swaps its edit tool for a patch tool on GPT models; Aider picks a format per model, defaulting to whole-file. Aider's own benchmark has one model run both ways: **Qwen2.5-Coder-32B** (an older relative of our model, Qwen3-Coder) solved **16.4%** of tasks sending whole files vs **8.0%** with find-and-replace blocks, and its find-and-replace replies were well-formed only **71.6%** of the time (vs 99.6%). |

**One agent at a time:**

| Tier | Agent | How the model changes a file | Source |
|---|---|---|---|
| Small scale | **learn-claude-code** | Two tools: `write_file` (whole file) and `edit_file` (*"Replace exact text in a file once"*): error if the old text isn't there, otherwise replaces the **first** match, no uniqueness check. Both go through its folder check. | [`s02_tool_use/code.py:98-117, 143-146`](https://github.com/shareAI-lab/learn-claude-code/blob/7226f555d48900076eba126acf37c9ed5f002b5d/s02_tool_use/code.py#L98-L117) |
| Small scale | **ghuntley** | One `edit_file(path, old_str, new_str)`. The old text must appear **exactly once** (*"old_str found N times in file, must be unique"*). Empty old text creates a missing file, or appends to an existing one. | [`edit_tool.go:412-456`](https://github.com/ghuntley/how-to-build-a-coding-agent/blob/fa3dd49fdddf45e92b35c66746e6bb6aac6ac27e/edit_tool.go#L412-L456) |
| Small scale | **mini-swe-agent** | **No edit tool:** the prompt teaches `sed -i 's/old/new/'` and `cat <<'EOF' > file` through its shell tool. | [`config/default.yaml:60-90`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/config/default.yaml#L60-L90) |
| Industry | **Gemini CLI** | `replace` (old/new text, exactly one match unless `allow_multiple`) plus `write_file`. On a miss it tries looser matches in order: exact, flexible whitespace, regex, fuzzy. If all fail, a **second model call repairs the old/new pair**. Separate errors for "not found" (with *"use ReadFile to inspect the target lines before retrying"*) and "found N". | [`edit.ts:306-345, 369-379, 595-600`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/edit.ts#L306-L379); [`default-legacy.ts:351-359`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/definitions/model-family-sets/default-legacy.ts#L351-L359) |
| Industry | **Codex CLI** | **One `apply_patch` tool with its own patch format** (`*** Begin Patch`, `*** Update File: path`, then `-` and `+` lines). Context lines are matched with decreasing strictness: exact, then ignoring trailing spaces, then all outer spaces, then fancy punctuation. | [`default.md:132`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/protocol/src/prompts/base_instructions/default.md#L132); [`seek_sequence.rs:1-12`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/apply-patch/src/seek_sequence.rs#L1-L12) |
| Industry | **opencode** | `edit(path, oldString, newString, replaceAll)` plus `write`. Exactly one match unless `replaceAll`; on a miss it retries ignoring fancy quotes, dashes and spaces, then trailing whitespace, and otherwise returns a **hint with the closest lines**. **For GPT models it removes `edit` and `write` and offers a patch tool instead.** | [`edit.ts:24-34, 194-199, 276`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/tool/plugin/edit.ts#L24-L34); [`patch.ts:319-328`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/tool/plugin/patch.ts#L319-L328) |
| Industry | **OpenHands** | One `file_editor` tool with commands `view`, `create`, `str_replace`, `insert`, `undo_edit`. `str_replace` needs exactly one match (else *"Multiple occurrences ... in lines [...]"*), retries once with outer whitespace stripped, and keeps history for undo. `create` **refuses to overwrite** an existing file. | [`definition.py:26`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/file_editor/definition.py#L26); [`editor.py:234-258, 682-688`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/file_editor/editor.py#L234-L258) |
| Industry | **Aider** | **No tool calls: the model writes edits in its reply text** in one of several formats. *"whole"*: the full updated file (the default for models Aider doesn't know). *"diff"*: SEARCH/REPLACE blocks. Also unified diffs and others, chosen per model. | [`models.py:131`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/models.py#L131); [`edit-formats.md`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/docs/more/edit-formats.md); benchmark rows [`polyglot_leaderboard.yml:209-218, 365-374`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/website/_data/polyglot_leaderboard.yml#L209-L218) |
| Closed (docs) | **Claude Code** | `Edit`: *"exact string replacement. It takes an `old_string` and a `new_string` ... It doesn't use regex or fuzzy matching."* The old text *"must appear exactly once"*, unless `replace_all`. Claude must have read the file first. Plus `Write`, which *"Creates or overwrites files"*. | [Tools reference](https://code.claude.com/docs/en/tools) (public docs, read 2026-11-24) |

**What they agree on → what we follow:** a tool where the model sends **the exact old text and the new text**; the old text must appear **exactly once**; and a failure comes back as an **error that says which failure** (missing or repeated) and what to do next.

**Where they differ:** how forgiving the match is (exact only vs a cascade of looser matches), whether a separate whole-file tool exists, and whether the format changes with the model. These are the options and decisions in section 3.

**Cross-check with a survey.** The *Harness Engineering* survey ([Barbaste et al., July 2026](https://arxiv.org/abs/2609.00006)) compares editing in 11 agents (Table 7, p.28) and agrees on the families above. Its Recommendation 5 (p.68): *"Match your edit-tool contract to your model tier: exact unique-substring replacement for frontier models, a fuzzy cascade for open or weaker models"*, and avoid line-number-based edits, since *"models drift on line numbers more than on contextual matching."* One difference: it describes opencode's matcher as a nine-stage cascade; the source we read today has only the two looser passes listed above. The survey is a July snapshot, so the source wins.

### 3. Sub-steps and decisions, derived top-down

**The options the research gives**, by what the model sends:

| Option | Who | What the model sends |
|---|---|---|
| **A. The whole new file** | Aider ("whole"), and every `write_file` tool | The full file, with the fix |
| **B. Find-and-replace** | learn-claude-code, ghuntley, Gemini CLI, opencode, OpenHands, Claude Code | The exact old text and its replacement |
| **C. A patch** | Codex, opencode (GPT models), Aider ("udiff") | A diff in a custom format |
| **D. A shell command** | mini-swe-agent | `sed -i 's/old/new/' file` |

**Filter by this project's level of complexity:**

- **D (shell): dropped.** There's no terminal tool yet, and a shell command would get around the folder check anyway.
- **C (patch): dropped.** A custom format needs a parser of its own, and models are trained for specific dialects (Codex's is GPT-specific).
- **A and B: both simple.** A is the most forgiving for weaker models (Aider's Qwen numbers). B is what almost every tool-calling agent uses, sends far less text, and can't accidentally drop the rest of the file. This is decision A below.

**Within option B, the choices:**

| Choice | What the agents do | Result |
|---|---|---|
| Must the old text appear exactly once? | All but learn-claude-code | **Settled:** yes; several matches is an error. No "replace all" flag (the demo fixes one line). |
| Forgiving matches (ignore whitespace, punctuation, ask a second model)? | Codex, opencode, Gemini CLI, partly OpenHands | **Dropped:** a cascade is real complexity. Exact matching, as in learn-claude-code, ghuntley and Claude Code. If our model keeps missing, that's a measured question for the Phase 2 benchmark, not a guess now. |
| What comes back on failure? | Separate "not found" and "found N times" errors, with advice | **Settled:** two distinct errors, each saying what to do ("read the file and copy the text exactly", "add surrounding lines so it's unique"). |
| What comes back on success? | A short confirmation (learn-claude-code) or the edited lines (OpenHands) | **Settled, Claude's judgment:** a short confirmation, the simplest. |
| Stay inside the project | Every agent with file tools checks paths | **Settled:** call `inside_project` from step 3, as noted in its coverage check. |
| A separate tool to create or overwrite files? | Most have one; ghuntley and OpenHands handle creation differently | **Decision B** |

**Decisions (agreed 2026-11-26, both as Claude leaned):**

- **Decision A: find-and-replace, or send the whole file?** My lean: **find-and-replace.** It's what almost every agent with tool calls uses, Claude Code included, and our model (Qwen3-Coder, 480B) is far larger and newer than the 32B Qwen in Aider's comparison. That comparison is a good warning, though, so "whole file vs find-and-replace on our model" goes on the experiment list for the Phase 2 benchmark.
- **Decision B: also a tool to create or overwrite whole files?** My lean: **not now.** The Phase 1 goal only needs changing an existing line, and a whole-file write is easy to add later as its own tool when something needs it (e.g. the agent writing a new test).

**Sub-step** (one feature, so one sub-step; it's a brand-new tool, so there's no as-is cell):

| # | Sub-step | Based on |
|---|---|---|
| 4a | **Build `edit_file(filename, old_text, new_text)` and test it.** Registered like any other tool. Its description tells the model the old text must be copied exactly from the file and appear once. Test it without the model: a normal edit, text not found, text found twice, a path outside the folder. Then with the model: ask for a small change to a file in `sandbox/` and watch it read the file, then edit it; the cell puts the file back afterwards. | Option B; the "settled" rows above; ghuntley's uniqueness check; the folder check from step 3 |

### 4. Coverage check: the breakdown against the sub-step

| Part of the problem | Covered by |
|---|---|
| Change part of an existing file | **4a** |
| Create a new file | **Not now** (decision B); added when a later step needs it |
| Rewrite a whole file | **Not built** (decision A); queued as a Phase 2 benchmark experiment against find-and-replace |
| Delete or rename | **Dropped:** not needed for the Phase 1 goal |
| Old text not in the file | **4a:** "not found" error with advice; forgiving matches dropped |
| Old text appears more than once | **4a:** "found N times" error with advice |
| Edit outside the project | **4a** calls `inside_project` |
| A change you didn't want | **Deferred** to the approval prompt step. Until then, edits happen without asking, but only inside `sandbox/` |

### 5. Done when

- Asked for a small change to a file in `sandbox/`, the agent reads the file, calls `edit_file`, and the file on disk changes.
- `edit_file` refuses missing text, repeated text and a path outside the folder, each with an error that says what to do.
- Adding the tool needed nothing but `register()`.

---

## Step 5: Approval prompt

*Agreed 2026-11-26: decision A ask before every edit, decision B Enter to allow or type a reason to refuse.*

### 1. What we're doing and why

**The goal in one sentence:** before the agent does anything that changes something, show you the action and wait for your yes or no. This is the "asks before anything risky" part of Phase 1's goal, and the roadmap puts it before terminal commands on purpose ([`ROADMAP.md:74`](../ROADMAP.md)): *"Ask before risky actions, needed before shell access."* Once the agent can run commands, a command can get around the folder check, so your yes or no becomes the only guard.

Today nothing asks. In the agent loop (`ask()`, section 1f of the notebook), a tool call goes straight to `result = run_tool(name, args)`. The edit tool's live run (section 4a) showed it: the model asked for `edit_file`, and the file changed without anyone being asked.

**The problem broken down (MECE).**

*By what a tool does:*

| Kind of tool | Our tools | Live today? | Ask? |
|---|---|---|---|
| **Only looks** | `find_files`, `read_file` | ✅ | No: nothing changes |
| **Changes files** | `edit_file` | ✅ | The question of this step |
| **Runs commands** | The terminal-command tool, the next roadmap step | ❌ | Yes, when it's built: it reuses this step's prompt |

*By your answer:*

| Your answer | What should happen |
|---|---|
| **Yes** | The tool runs, as today |
| **No** | The tool doesn't run, and the model has to be told, or it will think the change happened |

### 2. Evidence: how real agents do it

Source code read on 2026-11-26 from local clones, links pinned to the commit read. **This is a snapshot:** these repos change daily.

**By question:**

| Question | What real agents do |
|---|---|
| What gets asked? | **Tools that only look are never asked:** Claude Code's permission table says read-only tools need no approval; Gemini CLI marks read, search and fetch tools as read-only. **Edits split the agents.** Asked by default: Gemini CLI, Claude Code, and opencode (whose fallback, when no rule matches, is to ask). Not asked inside the project: Codex (auto-approved when the patch stays in its writable folders, which its OS sandbox enforces), learn-claude-code (asks only when a rule flags danger, such as writing outside the workspace), Aider (applies edits to files you added, commits each one to git, and offers `/undo`), and OpenHands (never confirms by default; it runs in a container). **Commands are asked for almost everywhere:** Claude Code, mini-swe-agent, Aider (*"Run shell command?"*), Codex depending on its policy. |
| What can you answer? | **Just yes or no:** learn-claude-code (`Allow? [y/N]`). **No, with a reason for the model:** mini-swe-agent (Enter confirms; anything you type rejects, and becomes the message), opencode, Claude Code. **Yes for the rest of the session:** Codex, Gemini CLI, opencode, Claude Code (for edits, until the session ends). **Stop everything:** Codex's "Abort", and Claude Code stops the turn on a "No" without a comment. |
| What does the model get on "no"? | **A tool result saying it was refused**, so it knows the action didn't happen: *"Permission denied."* (learn-claude-code), *"Action rejected: ..."* (OpenHands), *"Commands not executed. The user rejected your commands with the following message: ..."* (mini-swe-agent), *"User denied execution."* (Gemini CLI). opencode and Claude Code pass your comment on as the reason. Codex distinguishes "denied, try something else" from "abort, wait for the user". |
| Can asking be turned off? | **Yes, as "modes", in most industry agents:** Gemini CLI (default, autoEdit, yolo, plan), Claude Code (six modes, from asking for most actions to skipping prompts), mini-swe-agent (human, confirm, yolo), Codex (approval policies, including "never"). OpenHands has a third way: `ConfirmRisky` asks only when **the model's own rating** of an action's risk is high enough. |
| Where does the check sit? | **Between "the model asked for a tool" and "run it".** learn-claude-code describes it as *"Only one line added to the agent loop: if not check_permission(block): continue"*. |

**One agent at a time:**

| Tier | Agent | Approval | Source |
|---|---|---|---|
| Small scale | **learn-claude-code** | A whole lesson (`s03_permission`): three gates before a tool runs: a hard deny list for commands, rules (writing outside the workspace, destructive commands), and `input("Allow? [y/N]")` when a rule matches. A refusal returns *"Permission denied."* to the model. | [`s03_permission/code.py:1-23, 176-199, 235-241`](https://github.com/shareAI-lab/learn-claude-code/blob/7226f555d48900076eba126acf37c9ed5f002b5d/s03_permission/code.py#L176-L199) |
| Small scale | **ghuntley** | **None:** tools run as soon as the model asks. | (no approval code found) |
| Small scale | **mini-swe-agent** | Modes `human`, `confirm` (the default) and `yolo`. In confirm mode, Enter runs the command; typing anything else rejects it and sends *"Commands not executed. The user rejected your commands with the following message: ..."* | [`agents/interactive.py:5-6, 25, 162-182`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/agents/interactive.py#L162-L182) |
| Industry | **Gemini CLI** | Policy rules decide per tool: `replace` and `write_file` default to **ask**, and are allowed outright in `autoEdit` mode. The answers: proceed once, proceed always (several variants), modify in an editor, or cancel. On cancel: *"User denied execution."* | [`policies/write.toml:30-40`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/policy/policies/write.toml#L30-L40); [`tools.ts:1109-1148`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/tools.ts#L1109-L1148); [`scheduler.ts:766-776`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/scheduler/scheduler.ts#L766-L776); [`types.ts:48-53`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/policy/types.ts#L48-L53) |
| Industry | **Codex CLI** | Approval policies: `UnlessTrusted`, `OnRequest` (*"The model decides when to ask"*), `Granular`, `Never`. Edits inside its writable folders are auto-approved, because its OS sandbox backs them. Your answer: approved, approved for the session, **denied** (*"continue the session and try something else"*) or **abort** (*"not do anything until the user's next command"*). | [`protocol.rs:1185-1207, 4573-4607`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/protocol/src/protocol.rs#L4573-L4607); [`safety.rs:100-123`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/core/src/safety.rs#L100-L123) |
| Industry | **opencode** | Rules say allow, ask or deny per action; with no matching rule, it **asks**. Your answer: once, always, or reject. Reject with a message turns your message into the error the model sees; without one, a plain "declined". | [`permission.ts:59-67, 86-95, 298-330`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/permission.ts#L298-L330) |
| Industry | **OpenHands** | **Never confirms by default** (`NeverConfirm`; the container is the safety net). Options: `AlwaysConfirm`, or `ConfirmRisky`, which asks only above a risk threshold, where the risk is a `security_risk` field **the model fills in itself** (*"The LLM's assessment of the safety risk of this action"*). A rejection reaches the model as *"Action rejected: ..."*. | [`confirmation_policy.py:27-60`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-sdk/openhands/sdk/security/confirmation_policy.py#L27-L60); [`state.py:180`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-sdk/openhands/sdk/conversation/state.py#L180); [`tool.py:893-897`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-sdk/openhands/sdk/tool/tool.py#L893-L897) |
| Industry | **Aider** | **Edits to files you added are applied without asking,** each one committed to git, with `/undo` to revert. It asks before creating a file (*"Create new file?"*), editing a file you didn't add, and running shell commands (*"Run shell command?"*). | [`base_coder.py:2207, 2226, 2450-2460`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2191-L2238); [`commands.py:553`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/commands.py#L553) |
| Closed (docs) | **Claude Code** | Read-only tools: no approval. File edits: approval required, and *"Yes, and don't ask again"* lasts *"Until session end"*. Bash: approval required, and "don't ask again" is saved per repository. On **No**: *"Claude Code sends your comment to Claude as the reason for the denial, and Claude continues working. If you select No without a comment ... Claude Code stops the turn."* Six permission modes, from `default` to `bypassPermissions`. | [Permissions docs](https://code.claude.com/docs/en/permissions) (public docs, read 2026-11-26) |

**What they agree on → what we follow:** tools that only look are never asked; a refusal goes back to the model as a tool result, so it knows the action didn't happen; and the check sits in the loop, between the model's request and running the tool.

**Where they differ:** whether edits inside the project are asked at all (agents with an OS sandbox or git undo skip it), what you can answer beyond yes and no, and whether asking can be switched off.

**Cross-check with a survey.** The *Harness Engineering* survey ([Barbaste et al., July 2026](https://arxiv.org/abs/2609.00006)), Recommendation 9 (p.69): for a developer tool, *"implement a three-mode approval system (PLAN / DEFAULT / YOLO) with permission-scope patterns."* Modes are dropped below as polish; the survey's own evidence is the agents in the table.

### 3. Sub-steps and decisions, derived top-down

**The options, by what gets asked:**

| Option | Who | Fits us? |
|---|---|---|
| **A. Ask before every tool call** | Nobody | **Dropped:** asking before every file read is noise. |
| **B. Ask before every tool that changes something** | Gemini CLI, Claude Code, opencode (fallback) | Decision A |
| **C. Ask only when a rule flags danger** | learn-claude-code, Codex (inside the sandbox), Aider (files you added) | Decision A |
| **D. Ask when the model rates its own action as risky** | OpenHands (`ConfirmRisky`) | **Dropped for now:** interesting for AI safety (the model judging its own risk), noted for later, not Phase 1. |

**Filter by this project's level of complexity:**

| Choice | Result |
|---|---|
| Read-only tools ask? | **Settled:** no, as every agent agrees. |
| Where the check sits | **Settled:** one check in `ask()`, between parsing the tool call and `run_tool`, as learn-claude-code does. |
| How the loop knows which tools change things | **Settled, Claude's judgment:** a set of tool names in the notebook, `RISKY_TOOLS = {"edit_file"}`; the terminal tool joins it when it's built. (Gemini CLI tags each tool with a kind; a set is the minimal version.) |
| "Yes for the rest of the session" and modes (auto-edit, yolo) | **Dropped:** convenience. The roadmap lists permission modes as skip and permission rules as later. |
| "Abort" (stop the whole turn) | **Dropped:** a refusal goes back to the model, which decides what to do next. |
| What you can answer | **Decision B** |

**Decisions (agreed 2026-11-26, both as Claude leaned):**

- **Decision A: ask before every edit, or only when a rule flags danger?** My lean: **every edit** (option B). Phase 1's goal says the agent "asks before anything risky", and the agents that skip asking inside the project (Codex, Aider, OpenHands) do so because they have an OS sandbox, git undo, or a container behind them. We have none of those.
- **Decision B: what can you answer?** My lean: **mini-swe-agent's single prompt.** Press Enter (or type `y`) to allow; type anything else to refuse, and what you typed goes to the model as the reason, e.g. *"no, change greet instead"*. One prompt gives both a plain no and a no-with-guidance, which is what Claude Code and opencode offer too. The alternative is learn-claude-code's plain `[y/N]`.

**Sub-step** (one feature, so one sub-step):

| # | Sub-step | Based on |
|---|---|---|
| 5a | **Build the approval prompt and test it.** `RISKY_TOOLS`, an `approve(name, args)` function that shows the tool call and reads your answer with `input()`, and a new `ask()`: section 1f's version plus the check before `run_tool` (changed lines marked). Then run the edit request from section 4a twice, and **you answer the prompt** in the notebook: once yes (the file changes), once with a reason (the file stays the same, and we see what the model does with your reason). A read along the way must not ask. | learn-claude-code's "one line in the loop"; mini-swe-agent's prompt; the "settled" rows above |

**No as-is cell:** the "before" is already in the notebook. Section 4a's live run shows the model editing without being asked, and section 1f has the `ask()` being changed. (Claude's judgment, to keep the cell count down.)

### 4. Coverage check: the breakdown against the sub-step

| Part of the problem | Covered by |
|---|---|
| Tools that only look | **5a:** not in `RISKY_TOOLS`, so never asked; checked during the test |
| Tools that change files | **5a:** `edit_file` is asked about |
| Tools that run commands | **Deferred** to the terminal-command step: its tool joins `RISKY_TOOLS` |
| Your "yes" | **5a:** the tool runs |
| Your "no" | **5a:** the tool doesn't run; the model gets a refusal with your reason |
| Session-wide yes, modes, rules, model-rated risk | **Dropped** for Phase 1 (see the filter); model-rated risk noted for later |

### 5. Done when

- An edit stops and shows you the tool call; your yes applies it.
- Typing a reason refuses it: the file is unchanged, and the model receives your reason.
- Reading a file never prompts.

---

## Step 6: Run shell commands

*Agreed 2026-11-26: decision A approve every command, decision B a fixed 30 s limit.*

### 1. What we're doing and why

**The goal in one sentence:** let the agent run a terminal command, such as `pytest`, and see its output. That serves two parts of Phase 1's goal: **seeing the failure** (a coding agent usually finds a bug by running the failing test and reading the error) and **"runs the tests to confirm the fix."** The roadmap ([`ROADMAP.md:75`](../ROADMAP.md)): *"Lets the agent run code, tests and git."*

Today the agent can find, read and edit files (each edit approved by you), but it can't run anything, so it can't see a test fail or pass.

**The problem broken down (MECE).**

*By what a command can do:*

| A command can... | Example | Limited by our code? |
|---|---|---|
| **Look** | `ls`, `cat`, `grep`, `git status` | No |
| **Run code** | `pytest`, `python script.py`, which can then do anything the code does | No |
| **Change files** | `sed -i`, `rm`, `git commit` | No |
| **Reach outside the project** | `cat ../ROADMAP.md`, network access | **No: it gets around the folder check from step 3** |

In short, a command can do anything your user account can. The only guard is the approval prompt from step 5: you see each command and say yes or no. That's a known limitation, not something to fix here; containers and OS sandboxes are out of scope for this project.

*By what the tool itself must handle:*

| Concern | The question |
|---|---|
| **Where** it runs | In which folder? |
| **How long** it may run | What stops a command that hangs, or waits for input forever? |
| **What comes back** | The output, the errors, and whether it succeeded (the exit code) |
| **How much** comes back | What if a command prints thousands of lines? |
| **Whether it may run at all** | The approval prompt (already built) |

### 2. Evidence: how real agents do it

Source code read on 2026-11-26 from local clones, links pinned to the commit read. **This is a snapshot:** these repos change daily.

**By question:**

| Question | What real agents do |
|---|---|
| A fresh process per command, or one long-lived terminal? | **Fresh process each time:** learn-claude-code, ghuntley, mini-swe-agent (*"Every action is executed in a new subshell"*), Claude Code (*"runs each command in a separate process"*; only `cd` carries over). **A long-lived terminal** that keeps `cd` and variables: OpenHands (a tmux session), Codex (optional sessions it can type into later). |
| What stops a hanging command? | **A fixed time limit:** learn-claude-code 120 s, mini-swe-agent 30 s, opencode 2 min, Claude Code 2 min (the model can ask for up to 10), Codex 10 s by default. **A limit on silence instead:** Gemini CLI stops a command after 5 minutes with no new output; OpenHands pauses after 30 s with no new output and lets the model wait longer or press Ctrl+C. |
| What comes back? | **Output and errors combined:** learn-claude-code, ghuntley, mini-swe-agent. **Plus the exit code** (0 means success): mini-swe-agent, Gemini CLI (*"Exit Code: N"*), Codex (*"Exit code"*, plus *"Wall time"*), OpenHands, opencode. |
| What if the output is huge? | **Cut it at a limit:** learn-claude-code (50,000 characters). **Keep the start and the end:** mini-swe-agent (over 10,000 characters, with a warning to use `head` or `tail`), Codex, Claude Code (for failed commands). **Save the full output to a file and show a preview:** opencode, OpenHands (over 30,000 characters), Claude Code. Gemini CLI can also have a second model summarize it. |
| Where does it run? | **In the project folder,** everywhere. Gemini CLI and opencode also check a requested working folder against the workspace. |
| Who approves commands? | **You, by default,** in mini-swe-agent (confirm mode), Aider, Claude Code (except a built-in list of read-only commands), Codex (depending on its policy). learn-claude-code blocks a short deny list (`sudo`, `rm -rf /`, ...). Codex and Gemini CLI also run commands inside an OS sandbox. |

**One agent at a time:**

| Tier | Agent | Shell tool | Source |
|---|---|---|---|
| Small scale | **learn-claude-code** | `bash(command)`: `subprocess.run(shell=True, cwd=WORKDIR, timeout=120)`, output and errors joined and cut at 50,000 characters; a short deny list (`sudo`, `rm -rf /`, ...) is checked first. | [`s02_tool_use/code.py:63-75`](https://github.com/shareAI-lab/learn-claude-code/blob/7226f555d48900076eba126acf37c9ed5f002b5d/s02_tool_use/code.py#L63-L75) |
| Small scale | **ghuntley** | `bash`: `exec.Command("bash", "-c", ...)` with combined output; **no time limit, no size limit.** | [`bash_tool.go:372-389`](https://github.com/ghuntley/how-to-build-a-coding-agent/blob/fa3dd49fdddf45e92b35c66746e6bb6aac6ac27e/bash_tool.go#L372-L389) |
| Small scale | **mini-swe-agent** | Its only tool. A new subshell per command, 30 s default time limit (it kills the whole process group), output with errors plus `returncode`; over 10,000 characters the model sees the head and tail with a warning. | [`environments/local.py:16, 24-29, 72-90`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/environments/local.py#L72-L90); [`config/default.yaml:39-40, 118-140`](https://github.com/SWE-agent/mini-swe-agent/blob/04d809ceab9df28f9adaed044884180159172930/src/minisweagent/config/default.yaml#L118-L140) |
| Industry | **Gemini CLI** | `run_shell_command`, with an optional working folder (checked against the workspace) and background mode. Stops after **5 minutes without output** (the timer resets on each new output). The model sees `Output: ...`, `Error: ...` and `Exit Code: N`; long output can be summarized by another model call. | [`shell.ts:702-709, 773-796, 1030-1044, 1239-1255`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/tools/shell.ts#L1030-L1044); [`config.ts:1321-1322`](https://github.com/google-gemini/gemini-cli/blob/b9776560ea5710bc673891499aaec68c737d160a/packages/core/src/config/config.ts#L1321-L1322) |
| Industry | **Codex CLI** | Default time limit **10 s** (the model can pass its own). Result: `Exit code`, `Wall time`, `Total output lines` when cut, then `Output`. Also a tool that runs a command in a terminal session and returns a session ID, so the model can type into it later. Commands run inside its OS sandbox. | [`exec.rs:62`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/core/src/exec.rs#L62); [`tools/mod.rs:95-117`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/core/src/tools/mod.rs#L95-L117); [`shell_spec.rs:92-96, 141`](https://github.com/openai/codex/blob/818bde09950cab06c18808f540037aa8e5d616a5/codex-rs/core/src/tools/handlers/shell_spec.rs#L92-L96) |
| Industry | **opencode** | `shell(command, workdir, timeout, background)`. Default **2 min** for foreground commands; on timeout: *"Retry with a larger timeout if the command is expected to take longer."* Large output is saved to a file with a preview. The working folder goes through the same folder check as file tools. | [`shell.ts:22, 40-56, 120-148, 195-224`](https://github.com/anomalyco/opencode/blob/a5518690fc5cfd57ea2abfb636ef03a9ce67fc51/packages/core/src/tool/plugin/shell.ts#L195-L224) |
| Industry | **OpenHands** | *"Run shell commands in a persistent terminal session"* (tmux). With no time limit set, it pauses after **30 s of no new output**: exit code `-1` means still running, and the model can send Ctrl+C or keep waiting. Output over 30,000 characters is cut and the full text saved to a file. | [`definition.py:1, 89-113, 150-156, 186-199`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/terminal/definition.py#L89-L113); [`constants.py:18, 31`](https://github.com/OpenHands/software-agent-sdk/blob/84ae396c3cfc3ecb35d7388547f10167b477771d/openhands-tools/openhands/tools/terminal/constants.py#L18-L31) |
| Industry | **Aider** | **No shell tool for the model:** the model *suggests* commands in its reply; you confirm (*"Run shell command?"*, explicit yes required), Aider runs them in the repo, then asks *"Add command output to the chat?"* So you decide what the model gets to see. | [`base_coder.py:2450-2492`](https://github.com/Aider-AI/aider/blob/5dc9490bb35f9729ef2c95d00a19ccd30c26339c/aider/coders/base_coder.py#L2450-L2492) |
| Closed (docs) | **Claude Code** | Bash: *"runs each command in a separate process"*; `cd` carries over only inside the project; variables don't. Default time limit 2 min, up to 10 when the model asks. Output inline up to about 30,000 characters, beyond that saved to a file with a preview; failed commands get a head-and-tail excerpt. Approval required, except a built-in set of read-only commands. | [Tools reference, "Bash tool behavior"](https://code.claude.com/docs/en/tools); [permissions](https://code.claude.com/docs/en/permissions) (public docs, read 2026-11-26) |

**What they agree on → what we follow:** run in the project folder; return the output **with errors and the exit code**; stop runaway commands with a time limit; keep huge output from flooding the model.

**Where they differ:** a fresh process vs a long-lived terminal, a total time limit vs a silence limit, how huge output is handled, whether the model can set its own time limit, and whether every command needs approval.

**Cross-check with a survey.** The *Harness Engineering* survey ([Barbaste et al., July 2026](https://arxiv.org/abs/2609.00006)), Recommendation 3 (p.68): *"Begin with just a bash tool."* We added it last on purpose, after the approval prompt, because a shell gets around every check in our own tool code.

### 3. Sub-steps and decisions, derived top-down

**The options, by how the agent gets to run commands:**

| Option | Who | Fits us? |
|---|---|---|
| **A. A tool that runs one command in a fresh process** | learn-claude-code, ghuntley, mini-swe-agent, Claude Code | ✅ The simplest |
| **B. A long-lived terminal session** (keeps `cd`, variables; can type into running programs) | OpenHands, Codex (optionally) | **Dropped:** a session manager is real complexity; the demo only runs `pytest`. |
| **C. The model suggests commands, you run them and decide whether it sees the output** | Aider | **Dropped:** the Phase 1 goal needs the agent to run the tests itself. |

**Within option A:**

| Choice | Result |
|---|---|
| Where it runs | **Settled:** in `sandbox/` (the folder the other tools use). |
| What comes back | **Settled:** the exit code plus output and errors combined, like mini-swe-agent. |
| A time limit | **Settled:** a fixed limit of 30 s, like mini-swe-agent; a timeout returns an error saying so. A silence-based limit (Gemini CLI, OpenHands) is dropped as more complex. |
| Huge output | **Settled, Claude's judgment:** cut at 10,000 characters, keeping the start and the end, like mini-swe-agent. Saving the full output to a file is dropped: the roadmap lists "large output handling" for later. |
| Background commands, typing into running programs | **Dropped:** the demo runs short commands. A command waiting for input is stopped by the time limit. |
| Which Python and pytest a command finds | **Settled, Claude's judgment:** commands run with the notebook's own Python first on the `PATH`. A check on 2026-11-26 found that a shell started from here picks Anaconda's base Python, and `python3` is the system 3.9, so tests could run in the wrong environment. |
| A deny list (`sudo`, `rm -rf /`) | **Dropped:** easy to get around (e.g. via another program), and every command already waits for your yes. The roadmap lists permission rules for later. |
| An OS sandbox | **Dropped:** out of scope for this project. |
| Approval | **Settled:** the tool joins `RISKY_TOOLS`, so every command goes through the approval prompt from step 5 (subject to decision A). |
| Can the model set the time limit? | **Decision B** |

**Decisions (agreed 2026-11-26, both as Claude leaned):**

- **Decision A: approve every command, or let "look-only" commands run without asking?** My lean: **every command.** Claude Code skips the prompt for a built-in list of read-only commands, but deciding what's read-only is harder than it looks: `cat notes.txt > app.py` starts with `cat` and overwrites a file. With every command shown to you, the boundary gap (a command can reach outside the project) is at least visible every time.
- **Decision B: can the model choose a longer time limit for a command?** My lean: **no, a fixed 30 s.** Claude Code, opencode, OpenHands and Codex let the model pass a timeout, which matters for slow builds and installs. Our demo's tests take seconds, and one fixed limit is one less thing to get right.

**Sub-step** (one feature, so one sub-step; a brand-new tool, so no as-is cell):

| # | Sub-step | Based on |
|---|---|---|
| 6a | **Build `run_command(command)` and test it.** Runs the command in `sandbox/` with a 30 s limit and the notebook's Python first on the `PATH`, returns the exit code and the combined output (start and end kept past 10,000 characters), registered and added to `RISKY_TOOLS`. Test it without the model: a command that works, one that fails (non-zero exit code), and one that runs too long. Then with the model, answering the approval prompts yourself: **(1)** put a tiny failing test in `sandbox/` and ask the agent to run the tests and say what fails; **(2)** ask it to show `../ROADMAP.md` with `cat`, and watch the approval prompt show a command that goes outside the project, which the folder check can't stop. | Option A; mini-swe-agent's limits and result; learn-claude-code's `subprocess.run`; the approval prompt from step 5 |

### 4. Coverage check: the breakdown against the sub-step

| Part of the problem | Covered by |
|---|---|
| Commands that look, run code, or change files | **6a:** the tool runs them, each after your yes |
| Commands that reach outside the project | **Not prevented** (a known limitation without an OS sandbox); **6a** makes it visible in test (2), and your yes or no is the guard |
| Where it runs | **6a:** `sandbox/` |
| How long | **6a:** 30 s fixed limit |
| What comes back | **6a:** exit code plus combined output |
| How much | **6a:** start and end past 10,000 characters |
| Whether it may run | **6a:** joins `RISKY_TOOLS` (decision A) |

### 5. Done when

- After your yes, the agent runs `pytest` in `sandbox/`, sees the failing test, and says what fails.
- A failing command returns its non-zero exit code and output; a command over 30 s is stopped with an error saying so.
- Every command waits for your yes, including one that reaches outside the project, which the folder check doesn't stop.
