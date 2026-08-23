# Skill evals

Behavioral scenarios for the skills in this repo. They test routing (does the right skill load for this phrasing, and stay out of the way for the phrasings its description excludes) and the shape of the resulting behavior.

These files sit outside `skills/*/` on purpose. Nothing here is loaded when a skill triggers, so the suite costs zero tokens at runtime.

## Files

| File | Contents |
|---|---|
| `tts.json` | 4 scenarios for `tts`, including one negative-trigger case |
| `explain-yourself.json` | 4 scenarios for `explain-yourself`, including one negative-trigger case |

## Scenario shape

Each file is a JSON object with `skill_name` and a `scenarios` array. Per scenario:

- `id`: stable identifier, suffixed `-negative` for a case that must not trigger the skill
- `query`: what the user types, verbatim
- `files`: paths the query refers to; `[]` when the query names no file
- `expect_trigger`: whether the named skill should load
- `expected_behavior`: prose description of the correct outcome
- `expectations`: individually checkable statements, each pass or fail with no partial credit
- `baseline_no_skill`: result of the same query run with no skills installed

The negative cases come straight from the negative-trigger language already in each skill's `description` frontmatter: `tts` excludes bare "say" / "tell me" idioms, and `explain-yourself` hands an already-prose document to `tts`.

## Running the suite

There is no harness. Each scenario is one prompt to a fresh Claude Code session, graded by reading the transcript against the scenario's `expectations`.

1. Start a session in a scratch directory with only this repo's `skills/` installed. Fresh means a new session with no prior turns: a session that has already discussed the skill will trigger it for reasons the eval is not measuring.
2. Create whatever `files` the scenario names. Contents matter only insofar as they match the description in the query (a markdown doc, a Python file, a prose ADR).
3. Paste `query` verbatim. Do not name the skill and do not rephrase.
4. Record, per scenario: whether the skill loaded, and pass/fail per entry in `expectations`.
5. A scenario passes only when `expect_trigger` matched observed behavior and every expectation passed.

Run each scenario at least twice. Routing is probabilistic, and a single trigger tells you less than two consistent ones.

## Baselines

`baseline_no_skill` records the same query run with the skills uninstalled, so a score credits the skill rather than the model's floor. A scenario the model already handles well with no skill installed is not evidence the skill works.

**Current state: every baseline in both files is unmeasured** (`"measured": false`). No no-skill run has been performed. Until they are filled in, scores from this suite are uncalibrated and should not be used to claim a skill improved anything.

To record one: run the scenario in a session with the skill removed from the skills directory, then set `measured` to `true`, `result` to `"pass"` or `"fail"`, and `notes` to what the model actually did.

## Relationship to `meta-skill-creator`

Anthropic's `meta-skill-creator` skill defines a similar eval format at `references/schemas.md`, using `prompt`, `expected_output`, `files`, and `expectations`. This suite uses `query`, `files`, and `expected_behavior` per the field names in the story that commissioned it, and keeps `expectations` from the `meta-skill-creator` shape along with its grading convention of pass/fail per expectation with no partial credit. The field names differ; the grading model does not. A future adapter to `meta-skill-creator`'s runner would be a rename of `query` to `prompt` and `expected_behavior` to `expected_output`.
