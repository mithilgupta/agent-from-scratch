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
