from pathlib import Path

import pytest
from glue_text import default_output_path, find_ordered_chunks


def write_chunks(tmp_path, contents_by_part_number):
    for number, text in contents_by_part_number.items():
        (tmp_path / f"doc-pass2-part{number:02d}.txt").write_text(text, encoding="utf-8")


def test_find_ordered_chunks_orders_by_part_number_not_alphabetically(tmp_path):
    # Given contiguous chunks whose numbers cross a digit-width boundary (9, 10, 11) —
    # alphabetical order would read "part10" and "part11" before "part9"
    write_chunks(tmp_path, {10: "tenth", 11: "eleventh", 9: "ninth"})

    # When the chunks are resolved from a glob pattern
    chunks = find_ordered_chunks(str(tmp_path / "doc-pass2-part*.txt"))

    # Then they come back in numeric order
    assert [c.read_text(encoding="utf-8") for c in chunks] == ["ninth", "tenth", "eleventh"]


def test_find_ordered_chunks_raises_on_missing_pattern_match(tmp_path):
    # Given no files matching the pattern
    # When resolving chunks
    # Then it raises rather than silently gluing nothing
    with pytest.raises(FileNotFoundError):
        find_ordered_chunks(str(tmp_path / "nothing-part*.txt"))


def test_find_ordered_chunks_raises_on_gap_in_sequence(tmp_path):
    # Given chunks 1 and 3 but no 2
    write_chunks(tmp_path, {1: "first", 3: "third"})

    # When resolving chunks
    # Then it raises rather than silently gluing an incomplete document
    with pytest.raises(ValueError, match="not contiguous"):
        find_ordered_chunks(str(tmp_path / "doc-pass2-part*.txt"))


@pytest.mark.parametrize(
    "pattern, expected",
    [
        pytest.param("doc-pass2-part*.txt", "doc-pass2.txt", id="strips_part_glob_suffix"),
        pytest.param("/tmp/out/doc-pass2-part*.txt", "/tmp/out/doc-pass2.txt", id="preserves_directory"),
    ],
)
def test_default_output_path(pattern, expected):
    # Given a glob pattern for numbered parts
    # When no explicit output path is given
    # Then the default path drops the "-partN" glob and keeps the rest
    # (compared as Path, not str, since Windows normalizes "/" to "\" on stringify)
    assert default_output_path(pattern) == Path(expected)
