#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Glue numbered text-file chunks back together in order.

Usage:
    python3 glue_text.py "<basename>-pass2-part*.txt" [--output OUTPUT_FILE]

Pass the glob pattern with the part number replaced by '*' (no digits typed in).
Matching files are found, ordered numerically by their partNN suffix (not
alphabetically, though the two agree for 2-digit numbers), and concatenated.
"""
import argparse
import glob
import re
from pathlib import Path

PART_RE = re.compile(r"-part(\d+)\.txt$")


def find_ordered_chunks(pattern: str) -> list[Path]:
    matches = [Path(p) for p in glob.glob(pattern)]
    if not matches:
        raise FileNotFoundError(f"No files matched pattern: {pattern}")

    numbered = []
    for path in matches:
        m = PART_RE.search(path.name)
        if not m:
            raise ValueError(f"File does not match the expected '-partNN.txt' naming: {path.name}")
        numbered.append((int(m.group(1)), path))

    numbered.sort(key=lambda pair: pair[0])

    numbers = [n for n, _ in numbered]
    expected = list(range(numbers[0], numbers[0] + len(numbers)))
    if numbers != expected:
        raise ValueError(f"Chunk numbers are not contiguous: found {numbers}")

    return [path for _, path in numbered]


def default_output_path(pattern: str) -> Path:
    stripped = re.sub(r"-part\*\.txt$", ".txt", pattern)
    return Path(stripped)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "pattern", help="Glob pattern with '*' in place of the part number, e.g. 'doc-pass2-part*.txt'"
    )
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    chunks = find_ordered_chunks(args.pattern)
    output_path = args.output or default_output_path(args.pattern)

    with output_path.open("w", encoding="utf-8") as out_f:
        for chunk_path in chunks:
            out_f.write(chunk_path.read_text(encoding="utf-8"))

    print(f"Glued {len(chunks)} chunk(s) into {output_path}:")
    for chunk_path in chunks:
        print(f"  {chunk_path.name}")


if __name__ == "__main__":
    main()
