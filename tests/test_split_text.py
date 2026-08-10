import pytest
from split_text import split_text

DOC_LINES = [f"line {n}\n" for n in range(1, 11)]  # 10 lines, golden fixture


def write_doc(tmp_path, name="doc-pass1.txt", lines=DOC_LINES):
    path = tmp_path / name
    path.write_text("".join(lines), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "lines_per_chunk, expected_chunk_count",
    [
        pytest.param(4, 3, id="uneven_split_rounds_up"),
        pytest.param(10, 1, id="single_chunk_when_chunk_size_covers_whole_file"),
        pytest.param(100, 1, id="chunk_size_larger_than_file"),
    ],
)
def test_split_text_writes_expected_chunk_count(tmp_path, lines_per_chunk, expected_chunk_count):
    # Given a 10-line document
    doc = write_doc(tmp_path)

    # When it is split at the given chunk size
    written = split_text(doc, lines_per_chunk, tmp_path, tag="pass1")

    # Then it produces the expected number of numbered chunk files
    assert len(written) == expected_chunk_count
    assert written[0].name == "doc-pass1-part01.txt"


def test_split_text_strips_trailing_pass_tag_from_basename(tmp_path):
    # Given an input file named with a trailing "-passN" tag
    doc = write_doc(tmp_path, name="report-pass2.txt")

    # When it is split with a different tag
    written = split_text(doc, lines_per_chunk=5, output_dir=tmp_path, tag="pass3")

    # Then the old pass tag is replaced, not doubled
    assert written[0].name == "report-pass3-part01.txt"


def test_split_text_preserves_line_content_across_chunks(tmp_path):
    # Given a document split into multiple chunks
    doc = write_doc(tmp_path)
    written = split_text(doc, lines_per_chunk=4, output_dir=tmp_path, tag="pass1")

    # When the chunks are concatenated back in order
    rejoined = "".join(p.read_text(encoding="utf-8") for p in written)

    # Then no content was lost or reordered
    assert rejoined == "".join(DOC_LINES)


def test_split_text_rejects_more_than_99_chunks(tmp_path):
    # Given a document that would need 100 single-line chunks
    lines = [f"{n}\n" for n in range(100)]
    doc = write_doc(tmp_path, lines=lines)

    # When splitting at one line per chunk
    # Then it raises rather than writing a 3-digit part number
    with pytest.raises(ValueError, match="exceeds 99"):
        split_text(doc, lines_per_chunk=1, output_dir=tmp_path, tag="pass1")
