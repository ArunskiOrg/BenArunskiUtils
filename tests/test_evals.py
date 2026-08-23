# SPDX-License-Identifier: MIT
"""Structural validation of the behavioral eval scenario files under evals/.

The scenarios are graded by hand, so nothing else would catch a scenario that lost a field, gained a
duplicate id, or came to point at a fixture that no longer exists.
"""

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_DIR = REPO_ROOT / "evals"
SKILLS_DIR = REPO_ROOT / "skills"

SCENARIO_KEYS = {
    "id",
    "query",
    "setup",
    "files",
    "expect_trigger",
    "expected_behavior",
    "expectations",
    "baseline_no_skill",
}
BASELINE_KEYS = {"measured", "result", "notes"}
BASELINE_RESULTS = (None, "pass", "fail")
MINIMUM_SCENARIOS = 3

EVAL_FILES = sorted(EVAL_DIR.glob("*.json"))
FILE_PARAMS = [pytest.param(path, id=path.stem) for path in EVAL_FILES]


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_every_skill_has_an_eval_file():
    # Given the skills published by this repo
    skills = {path.name for path in SKILLS_DIR.iterdir() if path.is_dir()}

    # When the eval files are discovered by name
    covered = {path.stem for path in EVAL_FILES}

    # Then each skill is covered, which also keeps the parametrized tests below from passing on an
    # empty set of files
    assert skills, "no skills found; the repo layout changed"
    assert skills <= covered


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_eval_file_parses_as_json(path):
    # Given an eval file
    # When it is parsed
    document = load(path)

    # Then it is an object carrying a skill name and a scenarios array
    assert isinstance(document, dict)
    assert document["skill_name"] == path.stem
    assert isinstance(document["scenarios"], list)


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_eval_file_holds_at_least_three_scenarios(path):
    # Given an eval file
    document = load(path)

    # When its scenarios are counted
    count = len(document["scenarios"])

    # Then it meets the per-skill minimum
    assert count >= MINIMUM_SCENARIOS, f"{path.name} has {count} scenarios"


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_scenario_ids_are_unique(path):
    # Given an eval file
    document = load(path)

    # When the ids are collected
    ids = [scenario["id"] for scenario in document["scenarios"]]

    # Then no id is reused, so a run record points at exactly one scenario
    assert len(ids) == len(set(ids)), f"duplicate ids in {path.name}: {ids}"


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_every_scenario_declares_the_documented_shape(path):
    # Given an eval file
    document = load(path)

    # When each scenario is checked against the shape evals/README.md documents
    # Then the key set matches exactly and every field carries the right type
    for scenario in document["scenarios"]:
        where = f"{path.name}:{scenario.get('id', '<no id>')}"
        assert set(scenario) == SCENARIO_KEYS, f"{where} has keys {sorted(scenario)}"
        assert isinstance(scenario["id"], str) and scenario["id"], where
        assert isinstance(scenario["query"], str) and scenario["query"], where
        assert isinstance(scenario["setup"], str) and scenario["setup"], where
        assert isinstance(scenario["expect_trigger"], bool), where
        assert isinstance(scenario["expected_behavior"], str) and scenario["expected_behavior"], where
        assert isinstance(scenario["files"], list), where
        assert scenario["expectations"] and isinstance(scenario["expectations"], list), where
        assert all(isinstance(item, str) and item for item in scenario["expectations"]), where


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_negative_trigger_case_is_present_and_named_as_one(path):
    # Given an eval file
    document = load(path)

    # When the scenarios that must not trigger the skill are selected
    negatives = [s for s in document["scenarios"] if not s["expect_trigger"]]

    # Then at least one exists and its id says so, so a run sheet cannot silently drop it
    assert negatives, f"{path.name} has no expect_trigger: false scenario"
    assert all(s["id"].endswith("-negative") for s in negatives)


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_scenario_files_exist_in_the_repo(path):
    # Given an eval file
    document = load(path)

    # When each referenced fixture path is resolved against the repo root
    missing = [
        name
        for scenario in document["scenarios"]
        for name in scenario["files"]
        if not (REPO_ROOT / name).is_file()
    ]

    # Then every one of them is committed, so two runners feed the model the same input
    assert not missing, f"missing fixtures referenced by {path.name}: {missing}"


@pytest.mark.parametrize("path", FILE_PARAMS)
def test_baseline_blocks_are_complete_and_internally_consistent(path):
    # Given an eval file
    document = load(path)

    # When each baseline block is checked
    # Then it declares the full key set, and a result is present only when a run was recorded
    for scenario in document["scenarios"]:
        baseline = scenario["baseline_no_skill"]
        where = f"{path.name}:{scenario['id']}"
        assert set(baseline) == BASELINE_KEYS, f"{where} baseline has keys {sorted(baseline)}"
        assert isinstance(baseline["measured"], bool), where
        assert baseline["result"] in BASELINE_RESULTS, where
        assert isinstance(baseline["notes"], str) and baseline["notes"], where
        if baseline["measured"]:
            assert baseline["result"] is not None, f"{where} is measured with no result"
        else:
            assert baseline["result"] is None, f"{where} records a result it did not measure"
