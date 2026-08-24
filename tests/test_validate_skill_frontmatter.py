import shutil
from pathlib import Path

import pytest
import validate_skill_frontmatter as validator

REPO_ROOT = Path(__file__).resolve().parent.parent
BAD_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "bad_skill" / "SKILL.md"


def write_skill(root: Path, slug: str, body: str) -> Path:
    skill_dir = root / "skills" / slug
    skill_dir.mkdir(parents=True)
    path = skill_dir / "SKILL.md"
    path.write_text(body, encoding="utf-8")
    return path


def frontmatter(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# heading\n\nbody\n"


def test_every_real_skill_file_passes():
    # Given the SKILL.md files actually shipped by this repository
    skill_files = validator.find_skill_files(REPO_ROOT)
    assert len(skill_files) >= 2

    # When each is validated
    # Then none of them reports a problem
    for path in skill_files:
        assert validator.validate_file(path) == [], path


def test_main_passes_against_the_repository_itself(capsys):
    # Given the repository root
    # When the validator runs the way CI runs it
    exit_code = validator.main([str(REPO_ROOT)])

    # Then it exits clean and names every file it checked
    assert exit_code == 0
    assert "passed validation" in capsys.readouterr().out


def test_bad_fixture_reports_every_violated_rule():
    # Given a SKILL.md that breaks every length, charset, reserved-word, and XML-tag constraint at once
    problems = validator.validate_file(BAD_FIXTURE)
    joined = " | ".join(problems)

    # When it is validated
    # Then each rule is reported separately rather than stopping at the first
    assert "over the 64-character limit" in joined
    assert "lowercase letters, digits, and hyphens" in joined
    assert "must not contain 'claude'" in joined
    assert "over the 1024-character limit" in joined
    assert "must not contain XML tags" in joined


def test_main_fails_the_build_on_the_bad_fixture(tmp_path, capsys):
    # Given a repository root whose only skill is the bad fixture
    skill_dir = tmp_path / "skills" / "bad-skill"
    skill_dir.mkdir(parents=True)
    shutil.copy(BAD_FIXTURE, skill_dir / "SKILL.md")

    # When the validator runs over it
    exit_code = validator.main([str(tmp_path)])

    # Then the build fails and the message names the offending file
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "skills/bad-skill/SKILL.md:" in stderr
    assert "1 of 1 SKILL.md file(s) failed validation" in stderr


@pytest.mark.parametrize(
    "body, expected_fragment",
    [
        pytest.param("# no frontmatter here\n", "no YAML frontmatter block", id="missing_fences"),
        pytest.param("---\nname: [unclosed\n---\n", "not valid YAML", id="unparseable_yaml"),
        pytest.param("---\njust a string\n---\n", "must be a mapping", id="not_a_mapping"),
        pytest.param("---\ndescription: fine\n---\n", "'name' is missing", id="missing_name"),
        pytest.param("---\nname: fine\n---\n", "'description' is missing", id="missing_description"),
        pytest.param("---\nname: 12\ndescription: d\n---\n", "'name' must be a string", id="name_not_string"),
        pytest.param(
            "---\nname: fine\ndescription: '   '\n---\n", "'description' is empty", id="blank_description"
        ),
        pytest.param(
            "---\nname: has_underscore\ndescription: d\n---\n",
            "lowercase letters, digits, and hyphens",
            id="name_charset",
        ),
        pytest.param(
            "---\nname: anthropic-tools\ndescription: d\n---\n",
            "must not contain 'anthropic'",
            id="name_reserved_word",
        ),
        pytest.param(
            "---\nname: fine\ndescription: uses <b>markup</b>\n---\n",
            "must not contain XML tags",
            id="description_xml_tag",
        ),
        pytest.param(
            "---\nname: fine\ndescription: closes with </b>\n---\n",
            "must not contain XML tags",
            id="description_closing_tag",
        ),
    ],
)
def test_each_rule_is_enforced(tmp_path, body, expected_fragment):
    # Given a SKILL.md that breaks exactly one rule
    path = write_skill(tmp_path, "sample", body)

    # When it is validated
    problems = validator.validate_file(path)

    # Then the matching message is reported
    assert any(expected_fragment in problem for problem in problems), problems


def test_html_comments_are_left_alone(tmp_path):
    # Given a description carrying an HTML comment but no tag
    path = write_skill(tmp_path, "sample", "---\nname: fine\ndescription: 'a <!-- note --> b'\n---\n")

    # When it is validated
    # Then it passes: hidden-content scanning belongs to a separate piece of work,
    # so the tag rule stops at tags
    assert validator.validate_file(path) == []


def test_length_limits_are_inclusive(tmp_path):
    # Given a name and description sitting exactly on their ceilings
    path = write_skill(tmp_path, "sample", frontmatter("a" * 64, "d" * 1024))

    # When they are validated
    # Then the boundary value is accepted
    assert validator.validate_file(path) == []


def test_one_character_over_each_limit_is_rejected(tmp_path):
    # Given a name and description one character past their ceilings
    path = write_skill(tmp_path, "sample", frontmatter("a" * 65, "d" * 1025))

    # When they are validated
    problems = validator.validate_file(path)

    # Then both limits are reported
    assert any("over the 64-character limit" in problem for problem in problems), problems
    assert any("over the 1024-character limit" in problem for problem in problems), problems


def test_safe_load_refuses_python_object_tags(tmp_path):
    # Given frontmatter carrying a YAML tag that the unsafe loader would instantiate
    path = write_skill(
        tmp_path, "sample", "---\nname: !!python/object/apply:os.system ['echo pwned']\n---\n"
    )

    # When it is validated
    problems = validator.validate_file(path)

    # Then safe_load rejects the tag as a parse error instead of constructing anything
    assert any("not valid YAML" in problem for problem in problems), problems


def test_missing_skills_directory_is_an_error(tmp_path, capsys):
    # Given a root with no skills/ directory
    # When the validator runs
    exit_code = validator.main([str(tmp_path)])

    # Then it fails loudly rather than reporting success over an empty set
    assert exit_code == 1
    assert "No skills/*/SKILL.md found" in capsys.readouterr().err
