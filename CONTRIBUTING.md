# Contributing

## Scope

This repo holds public Claude Code skills and small standalone utilities. A skill lives at `skills/<name>/` with a `SKILL.md`, a `README.md`, and any `reference/`, `agents/`, `scripts/`, or `resources/` it needs. Keep new skills self-contained: cross-skill dependencies should be named explicitly in the dependent skill's `SKILL.md` and `README.md` (see `explain-yourself`'s dependency on `tts` for the pattern).

## Adding a TTS engine to `tts`

`skills/tts/resources/bootstrap.py`'s `ENGINES` dict already tracks engines that aren't wired into rendering yet (see its entries' `note` fields). To finish one: add a `render_<engine>` path in `skills/tts/scripts/render.py`, add its id to `WIRED_ENGINES`, and cover it in `tests/test_render.py`. Don't add sign-up prose for API-key engines anywhere in the repo — that's generated at bootstrap time on purpose (see `SKILL.md`'s Bootstrap section), not stored.

## Ground rules

- No machine-specific paths, usernames, or environment assumptions. A skill must work for someone who has never seen this repo before, on macOS, Linux, or Windows.
- Prefer Python for anything beyond a one-line command; keep it in `scripts/`, invoked by the skill or its agents, so it's testable on its own.
- Python 3.9+, no third-party dependencies in `scripts/` beyond what a skill's `README.md` documents as a requirement (e.g. `edge-tts`).
- A script that depends on an external tool checks for it up front and fails with install instructions, not partway through.
- New `.py` files carry a `# SPDX-License-Identifier: MIT` line after the shebang (or as line 1 if there is none).

## Before opening a PR

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
```

(Windows: `.venv\Scripts\pip`, etc.) Both run in CI on every PR; a red check blocks merge.

If you're changing a skill's behavior, re-run it end to end in Claude Code and describe what you verified in the PR description — not just that tests pass.

## Tests

- One assertion's worth of behavior per test; name the test for the scenario, not the input values.
- Parametrize when multiple cases share the same action and differ only in input/expected output; give each case a name via `pytest.param(..., id=...)`.
- Given/When/Then comments in every test body.

## Changing a skill: observe, refine, test

Nothing in a `SKILL.md` is verifiable by reading it, so I don't edit one and call it done. I run a loop instead, with two Claude instances in different roles: Claude A, the session I watch while it works with the current skill, and Claude B, a separate session that tests whatever I changed. I repeat until a pass stops changing anything.

**Observe.** Give Claude A a task the skill is supposed to handle, then read the transcript rather than the answer. The answer is frequently fine while the skill is still wrong. Four things in a transcript mean the skill needs the edit, not the model:

- Unexpected exploration paths. The model opens files or runs searches the skill never mentioned. It is reconstructing context the skill should have handed it; say the thing it went looking for.
- Missed file-reference follow-throughs. The skill points at a `reference/` file and the model never opens it. Either the pointer doesn't say when to read it, or what's in there belongs inline.
- Overreliance on one section. Run after run loads the same bundled file for the same passage. Promote that passage into `SKILL.md` and drop the round trip.
- Ignored bundled files. A file goes unread across several runs. Cut it. An unread file still costs review attention and still rots.

**Refine.** Change one thing per pass, so the next observation attributes cleanly. Process notes like this section stay in `CONTRIBUTING.md`; `SKILL.md` is loaded on every trigger, and prose a contributor needs once is a permanent tax there.

**Test with Claude B.** Refining against the same session that produced the problem proves nothing, because that session already holds the context you were trying to encode. Hand the change to a fresh session with no memory of the discussion. `evals/` is that step: run the affected skill's scenarios as described under Behavioral evals below, and report the results in the PR.

## Behavioral evals

`evals/` holds scenarios that test skill routing: whether a phrasing loads the right skill, and whether the phrasings a `description` explicitly excludes stay excluded.

Run the affected skill's scenarios before merging any change that alters:

- a `description` in `skills/*/SKILL.md`, including wording that looks cosmetic. Routing is decided from that string, so a reworded clause is a behavior change.
- what a skill covers or refuses, whether or not the `description` changed.
- the relationship between skills, such as `explain-yourself` deferring an already-prose document to `tts`.

[`evals/README.md`](evals/README.md) has the scenario shape, the run procedure, the 2/2 pass rule, and the current baseline status. Follow it rather than improvising a run.

The merge gate: every scenario for each affected skill has been run, both runs are reported in the PR description, and no scenario fails. That includes the negative-trigger cases; a negative case that now fires the skill is a regression even when the resulting answer is good. A change that moves a scenario from pass to fail needs either a fix or an explicit note in the PR saying why the new behavior is correct and the scenario is being updated.

`tests/test_evals.py` validates the scenario files themselves and runs in CI, so a malformed or incomplete scenario fails the build. It checks structure, not behavior; it is no substitute for running the suite.

Adding a skill therefore means adding `evals/<name>.json` alongside it: CI fails a `skills/<name>/` directory that has no matching eval file. Each file needs at least three scenarios, at least one of them a negative case whose `id` ends in `-negative`, every path in a scenario's `files` committed under `evals/fixtures/`, and a `baseline_no_skill` slot per scenario that stays `"measured": false` until a run backs it.

## Commit and PR

Small, focused commits. PR description explains what changed and why, not just what.
