import json
import sys

import pytest
import resolve_source
from resolve_source import guess_kind, resolve_code, resolve_diff_file, resolve_directory


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


def test_guess_kind_identifies_a_real_directory(tmp_path):
    # Given a source path that is a real directory
    # When guessing the kind
    # Then it's classified as "directory", not "code"
    assert guess_kind(str(tmp_path)) == "directory"


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


def test_resolve_directory_concatenates_immediate_files_with_name_headers(tmp_path):
    # Given a directory with two files, sorted out of alphabetical write order
    (tmp_path / "b.tf").write_text("resource b", encoding="utf-8")
    (tmp_path / "a.tf").write_text("resource a", encoding="utf-8")

    # When resolving the directory
    text = resolve_directory(str(tmp_path))

    # Then each file appears once, alphabetically, under a name header
    assert text == "===== a.tf =====\nresource a\n\n===== b.tf =====\nresource b"


def test_resolve_directory_skips_subdirectories(tmp_path):
    # Given a directory containing both a file and a nested subdirectory
    (tmp_path / "top.tf").write_text("top level", encoding="utf-8")
    nested = tmp_path / "modules"
    nested.mkdir()
    (nested / "nested.tf").write_text("should not appear", encoding="utf-8")

    # When resolving the directory
    text = resolve_directory(str(tmp_path))

    # Then only the immediate file is included, per the documented "immediate files only" scope
    assert "top.tf" in text
    assert "nested.tf" not in text


def test_resolve_directory_exits_when_no_readable_files(tmp_path):
    # Given an empty directory
    # When resolving it
    # Then it exits with a clear message instead of writing an empty blob
    with pytest.raises(SystemExit, match="No files found"):
        resolve_directory(str(tmp_path))


def test_main_prints_output_path_and_kind_as_json(tmp_path, monkeypatch, capsys):
    # Given a diff file and CLI-style arguments
    diff_file = tmp_path / "changes.diff"
    diff_file.write_text("--- a/x\n+++ b/x\n", encoding="utf-8")
    output_file = tmp_path / "out.txt"
    monkeypatch.setattr(sys, "argv", ["resolve_source.py", str(diff_file), "-o", str(output_file)])

    # When running main()
    resolve_source.main()

    # Then it prints one JSON line the orchestrating skill can parse for `kind`,
    # without needing to open the resolved source file itself
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"output_path": str(output_file), "kind": "diff"}
