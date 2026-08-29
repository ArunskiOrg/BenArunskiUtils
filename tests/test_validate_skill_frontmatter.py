import shutil
from pathlib import Path

import pytest
import validate_skill_frontmatter as validator

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"
BAD_FIXTURE = FIXTURES / "bad_skill" / "SKILL.md"
OVERSIZED_FIXTURE_DIR = FIXTURES / "oversized_skill"
DEEP_REFERENCE_FIXTURE_DIR = FIXTURES / "deep_reference_skill"
MALFORMED_VERSION_FIXTURE_DIR = FIXTURES / "malformed_version_skill"


def install_fixture_skill(root: Path, fixture_dir: Path, slug: str) -> Path:
    """Copy a fixture skill folder into a repository root the validator can scan."""
    destination = root / "skills" / slug
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_dir, destination)
    return destination / "SKILL.md"


def body_of(line_count: int) -> str:
    lines = "\n".join(f"line {number}" for number in range(1, line_count + 1))
    return f"---\nname: fine\ndescription: d\nversion: 1.0.0\n---\n{lines}\n"


def write_skill(root: Path, slug: str, body: str) -> Path:
    skill_dir = root / "skills" / slug
    skill_dir.mkdir(parents=True)
    path = skill_dir / "SKILL.md"
    path.write_text(body, encoding="utf-8")
    return path


def frontmatter(name: str, description: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\nversion: 1.0.0\n---\n\n# heading\n\nbody\n"


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
        pytest.param(
            "---\ndescription: fine\nversion: 1.0.0\n---\n", "'name' is missing", id="missing_name"
        ),
        pytest.param(
            "---\nname: fine\nversion: 1.0.0\n---\n", "'description' is missing", id="missing_description"
        ),
        pytest.param(
            "---\nname: 12\ndescription: d\nversion: 1.0.0\n---\n",
            "'name' must be a string",
            id="name_not_string",
        ),
        pytest.param(
            "---\nname: fine\ndescription: '   '\nversion: 1.0.0\n---\n",
            "'description' is empty",
            id="blank_description",
        ),
        pytest.param(
            "---\nname: has_underscore\ndescription: d\nversion: 1.0.0\n---\n",
            "lowercase letters, digits, and hyphens",
            id="name_charset",
        ),
        pytest.param(
            "---\nname: anthropic-tools\ndescription: d\nversion: 1.0.0\n---\n",
            "must not contain 'anthropic'",
            id="name_reserved_word",
        ),
        pytest.param(
            "---\nname: fine\ndescription: uses <b>markup</b>\nversion: 1.0.0\n---\n",
            "must not contain XML tags",
            id="description_xml_tag",
        ),
        pytest.param(
            "---\nname: fine\ndescription: closes with </b>\nversion: 1.0.0\n---\n",
            "must not contain XML tags",
            id="description_closing_tag",
        ),
        pytest.param("---\nname: fine\ndescription: d\n---\n", "'version' is missing", id="missing_version"),
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
    path = write_skill(
        tmp_path, "sample", "---\nname: fine\ndescription: 'a <!-- note --> b'\nversion: 1.0.0\n---\n"
    )

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


@pytest.mark.parametrize(
    "version",
    [
        pytest.param("0.1.0", id="pre_one_release"),
        pytest.param("1.0.0", id="plain_release"),
        pytest.param("1.10.2", id="multi_digit_component"),
        pytest.param("2.0.0-rc.1", id="prerelease"),
        pytest.param("1.0.0+20260822", id="build_metadata"),
    ],
)
def test_semver_versions_are_accepted(tmp_path, version):
    # Given a SKILL.md whose version is a well-formed semver string
    path = write_skill(tmp_path, "sample", f"---\nname: fine\ndescription: d\nversion: '{version}'\n---\n")

    # When it is validated
    # Then the version raises no problem
    assert validator.validate_file(path) == []


@pytest.mark.parametrize(
    "version, expected_fragment",
    [
        pytest.param("1.2", "must be a semver string, got float", id="two_components_read_as_float"),
        pytest.param("'1.2'", "must be semver MAJOR.MINOR.PATCH", id="two_components_quoted"),
        pytest.param("1", "must be a semver string, got int", id="one_component_read_as_int"),
        pytest.param("v1.0.0", "must be semver MAJOR.MINOR.PATCH", id="leading_v"),
        pytest.param("'1.0.0.1'", "must be semver MAJOR.MINOR.PATCH", id="four_components"),
        pytest.param("'01.0.0'", "must be semver MAJOR.MINOR.PATCH", id="leading_zero"),
        pytest.param("'1.0.x'", "must be semver MAJOR.MINOR.PATCH", id="wildcard_component"),
    ],
)
def test_versions_that_are_not_semver_are_rejected(tmp_path, version, expected_fragment):
    # Given a SKILL.md whose version is not a semver string
    path = write_skill(tmp_path, "sample", f"---\nname: fine\ndescription: d\nversion: {version}\n---\n")

    # When it is validated
    problems = validator.validate_file(path)

    # Then the version rule fires and the message quotes the offending value
    assert any(expected_fragment in problem for problem in problems), problems


def test_malformed_version_fixture_fails_the_semver_rule():
    # Given a committed SKILL.md whose only violation is its version
    problems = validator.validate_file(MALFORMED_VERSION_FIXTURE_DIR / "SKILL.md")

    # When it is validated
    # Then the version rule is the one that fires
    assert len(problems) == 1
    assert "'version' must be a semver string" in problems[0]


def test_main_fails_the_build_on_the_malformed_version_fixture(tmp_path, capsys):
    # Given a repository root whose only skill has a malformed version
    install_fixture_skill(tmp_path, MALFORMED_VERSION_FIXTURE_DIR, "malformed-version-skill")

    # When the validator runs the way CI runs it
    exit_code = validator.main([str(tmp_path)])

    # Then the build fails and the message names the offending file
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "skills/malformed-version-skill/SKILL.md: 'version'" in stderr
    assert "1 of 1 SKILL.md file(s) failed validation" in stderr


def test_body_limit_is_inclusive(tmp_path):
    # Given a body sitting exactly on the 500-line ceiling
    path = write_skill(tmp_path, "sample", body_of(500))

    # When it is validated
    # Then the boundary value is accepted
    assert validator.validate_file(path) == []


def test_one_line_over_the_body_limit_is_rejected(tmp_path):
    # Given a body one line past the ceiling
    path = write_skill(tmp_path, "sample", body_of(501))

    # When it is validated
    problems = validator.validate_file(path)

    # Then the count and the limit are both named
    assert problems == ["body is 501 lines, over the 500-line limit"]


def test_oversized_fixture_fails_the_body_limit():
    # Given a committed SKILL.md whose only violation is its length
    problems = validator.validate_file(OVERSIZED_FIXTURE_DIR / "SKILL.md")

    # When it is validated
    # Then the body rule is the one that fires
    assert len(problems) == 1
    assert "over the 500-line limit" in problems[0]


def test_main_fails_the_build_on_the_oversized_fixture(tmp_path, capsys):
    # Given a repository root whose only skill has an oversized body
    install_fixture_skill(tmp_path, OVERSIZED_FIXTURE_DIR, "oversized-skill")

    # When the validator runs the way CI runs it
    exit_code = validator.main([str(tmp_path)])

    # Then the build fails and the message names the offending file
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "skills/oversized-skill/SKILL.md: body is" in stderr
    assert "1 of 1 SKILL.md file(s) failed validation" in stderr


def test_one_hop_reference_is_allowed(tmp_path):
    # Given a SKILL.md linking a reference file that links nothing further
    path = write_skill(
        tmp_path, "sample", "---\nname: fine\ndescription: d\nversion: 1.0.0\n---\n\n[guide](guide.md)\n"
    )
    (path.parent / "guide.md").write_text("# guide\n\nno onward links\n", encoding="utf-8")

    # When it is validated
    # Then one hop passes
    assert validator.validate_file(path) == []


def test_deep_reference_fixture_fails_the_depth_limit():
    # Given a committed skill whose reference forwards to a second file
    problems = validator.validate_file(DEEP_REFERENCE_FIXTURE_DIR / "SKILL.md")

    # When it is validated
    # Then the depth rule fires and the message spells out the chain
    assert problems == [
        "reference chain runs 2 hops from SKILL.md, over the 1-hop limit: "
        "reference/guide.md -> reference/details.md"
    ]


def test_main_fails_the_build_on_the_deep_reference_fixture(tmp_path, capsys):
    # Given a repository root whose only skill nests its references two deep
    install_fixture_skill(tmp_path, DEEP_REFERENCE_FIXTURE_DIR, "deep-reference-skill")

    # When the validator runs the way CI runs it
    exit_code = validator.main([str(tmp_path)])

    # Then the build fails and the message names the offending file
    assert exit_code == 1
    stderr = capsys.readouterr().err
    assert "skills/deep-reference-skill/SKILL.md: reference chain runs 2 hops" in stderr
    assert "1 of 1 SKILL.md file(s) failed validation" in stderr


def test_links_leaving_the_skill_folder_are_not_followed(tmp_path):
    # Given a SKILL.md pointing at a sibling skill that has its own nested references
    body = "---\nname: fine\ndescription: d\nversion: 1.0.0\n---\n\n[other](../other/README.md)\n"
    path = write_skill(tmp_path, "sample", body)
    other = tmp_path / "skills" / "other"
    other.mkdir(parents=True)
    (other / "README.md").write_text("[deeper](deeper.md)\n", encoding="utf-8")
    (other / "deeper.md").write_text("# deeper\n", encoding="utf-8")

    # When it is validated
    # Then the sibling skill's depth is left to the sibling skill
    assert validator.validate_file(path) == []


@pytest.mark.parametrize(
    "link",
    [
        pytest.param("[home](https://example.com/guide.md)", id="external_url"),
        pytest.param("[section](#requirements)", id="same_file_anchor"),
        pytest.param("[script](guide.py)", id="non_markdown_target"),
        pytest.param("[absent](missing.md)", id="target_that_does_not_exist"),
    ],
)
def test_targets_that_are_not_local_markdown_files_are_ignored(tmp_path, link):
    # Given a reference file whose onward link is not a local markdown file
    path = write_skill(
        tmp_path, "sample", "---\nname: fine\ndescription: d\nversion: 1.0.0\n---\n\n[guide](guide.md)\n"
    )
    (path.parent / "guide.md").write_text(f"# guide\n\n{link}\n", encoding="utf-8")

    # When it is validated
    # Then nothing counts as a second hop
    assert validator.validate_file(path) == []


def test_reference_cycles_terminate(tmp_path):
    # Given two reference files that link back to each other and to the SKILL.md
    path = write_skill(
        tmp_path, "sample", "---\nname: fine\ndescription: d\nversion: 1.0.0\n---\n\n[a](a.md)\n"
    )
    (path.parent / "a.md").write_text("[b](b.md)\n", encoding="utf-8")
    (path.parent / "b.md").write_text("[a](a.md)\n[skill](SKILL.md)\n", encoding="utf-8")

    # When it is validated
    # Then the walk stops instead of looping, reporting the one over-limit hop
    problems = validator.validate_file(path)
    assert problems == ["reference chain runs 2 hops from SKILL.md, over the 1-hop limit: a.md -> b.md"]


def test_missing_skills_directory_is_an_error(tmp_path, capsys):
    # Given a root with no skills/ directory
    # When the validator runs
    exit_code = validator.main([str(tmp_path)])

    # Then it fails loudly rather than reporting success over an empty set
    assert exit_code == 1
    assert "No skills/*/SKILL.md found" in capsys.readouterr().err
