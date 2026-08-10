import pytest
from resolve_source import guess_kind, resolve_code, resolve_diff_file


@pytest.mark.parametrize(
    "source, expected_kind",
    [
        pytest.param("482", "pr", id="bare_pr_number"),
        pytest.param("https://github.com/org/repo/pull/482", "pr", id="pr_url"),
        pytest.param("changes.diff", "diff", id="diff_extension"),
        pytest.param("changes.patch", "diff", id="patch_extension"),
        pytest.param("a1b2c3d", "commit", id="ref_that_is_not_a_file_or_number"),
    ],
)
def test_guess_kind_from_source_shape(source, expected_kind):
    # Given sources that do not correspond to an existing file
    # When guessing the source kind from its shape alone
    # Then it classifies by the documented resolution order
    assert guess_kind(source) == expected_kind


def test_guess_kind_prefers_pr_over_a_same_named_file(tmp_path, monkeypatch):
    # Given a source string that is both a bare number and a real file on disk
    real_file = tmp_path / "482"
    real_file.write_text("not a PR", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # When guessing the kind
    # Then the PR-number heuristic wins, per the resolution order documented in
    # SKILL.md ("Pull request" is checked before "Code")
    assert guess_kind("482") == "pr"


def test_resolve_code_returns_full_file_without_a_range(tmp_path):
    # Given a code file with no line range requested
    code_file = tmp_path / "sample.py"
    code_file.write_text("a = 1\nb = 2\nc = 3\n", encoding="utf-8")

    # When resolving it as a plain path
    text = resolve_code(str(code_file))

    # Then the whole file comes back verbatim, including its trailing newline
    assert text == "a = 1\nb = 2\nc = 3\n"


def test_resolve_code_returns_only_the_requested_line_range(tmp_path):
    # Given a code file and a path:START-END spec
    code_file = tmp_path / "sample.py"
    code_file.write_text("a = 1\nb = 2\nc = 3\nd = 4\n", encoding="utf-8")

    # When resolving lines 2 through 3 (1-indexed, inclusive)
    text = resolve_code(f"{code_file}:2-3")

    # Then only those lines are returned
    assert text == "b = 2\nc = 3"


def test_resolve_diff_file_returns_file_contents_verbatim(tmp_path):
    # Given a .diff file
    diff_file = tmp_path / "changes.diff"
    diff_file.write_text("--- a/x\n+++ b/x\n", encoding="utf-8")

    # When resolving it
    text = resolve_diff_file(str(diff_file))

    # Then it is used as-is, with no transformation
    assert text == "--- a/x\n+++ b/x\n"
