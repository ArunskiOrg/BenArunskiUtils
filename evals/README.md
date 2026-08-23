# Skill evals

Behavioral scenarios for the skills in this repo. They test routing (does the right skill load for this phrasing, and stay out of the way for the phrasings its description excludes) and the shape of the resulting behavior.

These files sit outside `skills/*/` on purpose. Nothing here is loaded when a skill triggers, so the suite costs zero tokens at runtime.

This file owns the run procedure and the current baseline status. [`CONTRIBUTING.md`](../CONTRIBUTING.md) owns the question of which changes require a re-run before merge.

## Files

| File | Contents |
|---|---|
| `tts.json` | 4 scenarios for `tts`, including one negative-trigger case |
| `explain-yourself.json` | 4 scenarios for `explain-yourself`, including one negative-trigger case |
| `fixtures/` | the documents and source file the scenarios refer to |

## Scenario shape

Each file is a JSON object with `skill_name` and a `scenarios` array. Per scenario:

- `id`: stable identifier, suffixed `-negative` for a case that must not trigger the skill
- `query`: what the user types, verbatim
- `setup`: the environment the scenario assumes before the query is pasted
- `files`: repo-relative paths the query refers to, all under `fixtures/`; `[]` when the query names no file
- `expect_trigger`: whether the named skill should load
- `expected_behavior`: prose description of the correct outcome
- `expectations`: individually checkable statements, each pass or fail with no partial credit
- `baseline_no_skill`: result of the same query run with no skills installed

`tests/test_evals.py` enforces this shape, including that every path in `files` exists, so a scenario cannot drift out of sync with the fixtures.

The negative cases come straight from the negative-trigger language already in each skill's `description` frontmatter: `tts` excludes bare "say" / "tell me" idioms, and `explain-yourself` hands an already-prose document to `tts`.

## Fixtures

Every path a `query` names resolves inside a checkout of this repo. That is the one execution model the suite supports: no scratch directory, no files created by hand, no per-runner variation in what the model reads. Routing depends partly on file content and length, so the inputs are committed rather than described.

`fixtures/src/render_media.py` is a standalone subprocess wrapper written for `ey-02`. It is not imported by anything and is not part of either skill.

## Running the suite

There is no harness. Each scenario is one prompt to a fresh Claude Code session, graded by reading the transcript against the scenario's `expectations`.

1. Check out the branch under test and install its `skills/`.
2. Start a session in that checkout. Fresh means a new session with no prior turns: a session that has already discussed the skill will trigger it for reasons the eval is not measuring.
3. Satisfy the scenario's `setup`.
4. Paste `query` verbatim. Do not name the skill and do not rephrase.
5. Record whether the skill loaded, and pass/fail per entry in `expectations`.

A single run passes when `expect_trigger` matched observed behavior and every expectation passed.

Run each scenario exactly twice, in two separate fresh sessions. **A scenario passes only on 2/2.** One pass and one fail is a fail, because routing is probabilistic and an intermittent trigger is the failure this suite exists to catch.

Per-run results are not stored in the JSON. Report both runs per scenario in the PR description, as `<id> run 1 / run 2` with the failing expectation named for any fail. The JSON holds the scenario definitions and the baselines; anything that changes on every run stays in the PR that ran it.

## Baselines

`baseline_no_skill` records the same query run with the skills uninstalled, so a score credits the skill rather than the model's floor. A scenario the model already handles well with no skill installed is not evidence the skill works.

**Current state: every baseline in both files is unmeasured** (`"measured": false`). No no-skill run has been performed. Until they are filled in, scores from this suite are uncalibrated and should not be used to claim a skill improved anything. The measurement is tracked as `ArunskiOrg/BenArunskiUtils-planning#28`.

To record one: run the scenario in a session with the skill removed from the skills directory, then set `measured` to `true`, `result` to `"pass"` or `"fail"`, and `notes` to what the model actually did. Never write a value without a run behind it; an invented baseline is worse than an absent one, because it silently calibrates every later score against nothing.

## Relationship to Anthropic's `skill-creator`

Anthropic's `skill-creator` skill defines its own eval format in [`skills/skill-creator/references/schemas.md`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/references/schemas.md). This suite is not runnable by that skill's tooling, and the gap is wider than naming:

| | `skill-creator` | this suite |
|---|---|---|
| File location | `evals/evals.json` inside the skill directory | `evals/<skill>.json` at the repo root, outside `skills/` |
| Array key | `evals` | `scenarios` |
| Identifier | unique integer `id` | string `id`, suffixed `-negative` for non-triggering cases |
| Query field | `prompt` | `query` |
| Outcome field | `expected_output` | `expected_behavior` |
| File paths | relative to the skill root | relative to the repo root |
| Extra fields | none | `setup`, `expect_trigger`, `baseline_no_skill` |

`expectations` and the grading convention it implies (pass or fail per statement, no partial credit) are the same in both, and that is the part worth keeping. The field names come from the story that commissioned this suite; the out-of-skill placement is deliberate, so the scenarios add zero tokens to what the model loads on trigger.

Porting to `skill-creator`'s runner would take more than a rename: `expect_trigger` has no counterpart there, since that runner assumes the skill under test is loaded and grades the output rather than the routing decision.
