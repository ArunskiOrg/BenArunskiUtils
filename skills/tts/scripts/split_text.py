#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Split a text file into fixed-size line chunks for parallel TTS preprocessing.

Usage:
    python3 split_text.py <input_file> [--lines-per-chunk N] [--output-dir DIR] [--tag TAG]

Writes <output-dir>/<basename>-<tag>-part<NN>.txt for each chunk, NN zero-padded
to 2 digits starting at 01 (max 99 chunks).
"""
import argparse
import re
from pathlib import Path

_TRAILING_PASS_TAG = re.compile(r"-pass\d+$")


def split_text(input_file: Path, lines_per_chunk: int, output_dir: Path, tag: str) -> list[Path]:
    basename = _TRAILING_PASS_TAG.sub("", input_file.stem)
    lines = input_file.read_text(encoding="utf-8").splitlines(keepends=True)

    chunks = [lines[i:i + lines_per_chunk] for i in range(0, len(lines), lines_per_chunk)]
    if len(chunks) > 99:
        raise ValueError(
            f"{len(chunks)} chunks exceeds 99 — 2-digit part numbers can't represent this. "
            "Increase --lines-per-chunk."
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for idx, chunk in enumerate(chunks, start=1):
        out_path = output_dir / f"{basename}-{tag}-part{idx:02d}.txt"
        out_path.write_text("".join(chunk), encoding="utf-8")
        written.append(out_path)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--lines-per-chunk", type=int, default=100)
    parser.add_argument("--output-dir", type=Path, default=None,
                         help="Defaults to the input file's own directory")
    parser.add_argument("--tag", default="pass1",
                         help="Label inserted before 'part' in each output filename (default: pass1)")
    args = parser.parse_args()

    output_dir = args.output_dir or args.input_file.parent
    written = split_text(args.input_file, args.lines_per_chunk, output_dir, args.tag)

    print(f"Wrote {len(written)} chunk(s):")
    for path in written:
        print(f"  {path}")


if __name__ == "__main__":
    main()
