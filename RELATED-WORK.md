# Related work

How this project compares to similar ones, checked against their actual repos
rather than from memory. **Checked on 2026-10-28**; these repos change often,
so re-check before relying on a row.

The question asked of each: does it **measure** the agent (a task benchmark,
model comparisons, token and cost tracking), or does it stop at "it works"?

## From-scratch coding agent tutorials

These are the tutorials surveyed in [INVENTORY.md](INVENTORY.md). For each one,
we searched the file tree and README for evals, benchmarks, metrics, model
comparisons and cost.

| Repo | Stars | Measures the agent? | Evidence |
|---|---|---|---|
| [shareAI-lab/learn-claude-code](https://github.com/shareAI-lab/learn-claude-code) | ~79k | **No** | No eval or benchmark files. Its "s17 Goal Loop" has an evaluator that decides when the loop may stop: an in-loop check (our *Goal check*), not a benchmark. |
| [decodingai-magazine/building-a-coding-agent-from-scratch-course](https://github.com/decodingai-magazine/building-a-coding-agent-from-scratch-course) | ~1k | **Yes, thoroughly** | `evals/`: 19 benchmark tasks (Terminal-Bench style, hidden test script writes a reward), a regression suite, LLM judges, Opik tracking. Reports pass@1, pass@k, pass^k, flakiness, tokens, seconds and dollars per trial. Its runbook (`running_the_code/05_evals.md`) runs two experiments: two models on the same tasks, and one model under two billing setups. |
| [labdmitriy/build-your-own-coding-agent](https://github.com/labdmitriy/build-your-own-coding-agent) | ~10 | **No** | No eval files; no measurement keywords in the README. |
| [SDiamante13/build-coding-agent-from-scratch](https://github.com/SDiamante13/build-coding-agent-from-scratch) | ~6 | **No** | Lists model prices and published benchmark scores to help pick a model, but doesn't measure its own agent. |
| [ghuntley/how-to-build-a-coding-agent](https://github.com/ghuntley/how-to-build-a-coding-agent) | ~6k | **No** | No eval files; no measurement keywords in the README. |

**Result: 4 of 5 don't measure; 1 (decodingai) does, in depth.** So "most
tutorials skip it" holds for this sample, but measurement is *not* unique to
this project, and decodingai is the closest prior work on it.

## Other related projects

| Repo | What it is | Relation to this project |
|---|---|---|
| [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | A ~100-line agent from the SWE-bench team, not a tutorial | Measured heavily on public benchmarks (SWE-bench, ProgramBench), and used to compare *models* on a fixed harness on the SWE-bench bash-only leaderboard. |
| [walkinglabs/learn-harness-engineering](https://github.com/walkinglabs/learn-harness-engineering) | A course on the files and process around agents you *use* (`AGENTS.md`, `feature_list.json`, progress logs, `init.sh`) with Claude Code or Codex | Doesn't build an agent; its "minimal harness loop" is a stub with no model call. Its Project 01 is a manual with/without comparison, with no benchmark or cost tracking. |

## What's still distinct about this project

Against the repos above only (not a full survey):

- **Measuring each component as it's added.** decodingai builds a full agent,
  then evaluates it (article 7 of 8) by varying the model and the provider.
  This project plans to build the benchmark right after the MVP (Phase 2) and
  use it to judge later changes. So far only one such before/after is
  scheduled (step 13), so this needs to become concrete to count.
- **Text protocol vs native tool calling** (step 13). Not seen in any repo above.
- **Small scale.** Notebooks with a few hundred lines, against decodingai's
  ~870 files with Opik, Modal and Docker. Same ideas, much lower entry cost.

Not yet checked: whether decodingai or others measure individual harness
components (ablations) anywhere outside the files read here.
