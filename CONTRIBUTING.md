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

## Versioning and the changelog

Every `skills/<name>/SKILL.md` carries a semver `version` in its frontmatter, and each skill is versioned on its own. Any PR that changes anything under `skills/<name>/` bumps that skill's `version` and adds a matching entry to `CHANGELOG.md` under the skill's heading, with the version, the date, and what changed. A PR that touches only repo-level files (tests, CI, `evals/`, this document) bumps nothing. A skill added later starts at `1.0.0` once it is published and installable; use a `0.x` version only while it is deliberately unfinished and you are telling installers not to rely on it yet.

Which component to bump, from the installer's position rather than a library's:

- **Major** for a breaking change: the skill is renamed or removed; the trigger `description` changes such that requests that used to route here no longer do, or requests that used to go elsewhere now land here; a bundled script is removed, renamed, or has its command-line contract changed; a new external dependency is required, or an existing one's minimum version rises (a tool on `PATH`, a Python package, an API key, an interpreter floor); the documented behavior in `SKILL.md` changes so that the same request produces a different result than before, such as a different output filename convention, a changed hand-off shape between the skill and its agents, or a changed order in which sources are resolved; or the skill drops support for an input it used to accept. What these share is that an existing installation stops behaving as it did, and re-reading the skill before updating is warranted.
- **Minor** for new capability that leaves existing behavior intact: a new supported input, a new bundled script, a `description` widened to cover phrasings that previously routed nowhere. Classify a `description` edit by what the [Behavioral evals](#behavioral-evals) show routing actually did, not by the size of the edit.
- **Patch** for corrections that change no contract: wording, typos, a bug fix in a script that restores documented behavior. If a change resists all three, treat it as Major and say why in the changelog entry. Classifying by elimination is how a break gets shipped as a patch.

Two cases the three components do not cover on their own:

- **A skill that depends on another skill.** `explain-yourself` uses `tts` when it is installed. Record the version it needs in its own `README.md` requirements, and bump the dependent skill whenever the version it needs rises: Major if it now requires a `tts` version an existing install would not have, Minor if the dependency stays optional and the skill still works without it. A Major in `tts` does not automatically bump `explain-yourself`; what matters is whether the dependent skill's own behavior changed.
- **A skill that is renamed or removed.** There is no frontmatter left to bump, so the record lives only in `CHANGELOG.md`. Give a removal its own entry under the old name stating the last shipped version and that it is gone. For a rename, close out the old name's entry, start the new name's history at the version the old name reached rather than back at `1.0.0`, and say in both entries that they are the same skill, so someone tracking an installed copy can follow it across the rename.

`scripts/validate_skill_frontmatter.py` rejects a missing or non-semver `version` and runs in CI, alongside two size limits it also enforces: a `SKILL.md` body is capped at 500 lines after the frontmatter, and every markdown file inside a skill's own folder that its `SKILL.md` can reach by links must sit at most one hop from it. Links leaving the folder are not followed, since the skill on the other end owns its own reference tree. Both limits bound what an agent loads before it can act, so content that outgrows them belongs in `README.md` or here rather than deeper in the reference tree.

## Before opening a PR

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m ruff check .
.venv/bin/python scripts/validate_skill_frontmatter.py
.venv/bin/python -m pytest
```

(Windows: `.venv\Scripts\pip`, etc.) All three run in CI on every PR; a red check blocks merge.

`requirements-dev.txt` pins `pytest`, `ruff`, and `pyyaml` to exact versions and is the only place those versions are written down. CI installs that same file, so a local run uses the identical tools and a new `ruff` release cannot turn a green PR red on its own. To take a newer version, edit `requirements-dev.txt`, run the four commands above, and fix whatever the new version reports in the same PR. `pytest` cannot move past 8.4.2 while Python 3.9 is the supported floor.

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
