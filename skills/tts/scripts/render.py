#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Render a speech-ready text file to MP3 with a neural TTS engine.

Standalone: works with or without Claude Code. Checks that the engine's CLI is
installed before rendering and fails with install instructions instead of
partway through a multi-minute render. Only edge-tts is wired up so far;
resources/bootstrap.py tracks other engines' prerequisites but rendering
through them isn't implemented here yet — see CONTRIBUTING.md.

Usage:
    python3 render.py <input.txt> [-o output.mp3] [--voice VOICE] [--rate RATE]
    python3 render.py --list-voices
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

DEFAULT_VOICE = "en-US-AndrewNeural"
DEFAULT_RATE = "-12%"

# Same skill-root-relative path resources/bootstrap.py writes to.
MARKER_PATH = Path(__file__).resolve().parent.parent / ".bootstrap-verified"
WIRED_ENGINES = {"edge-tts"}

INSTALL_HELP = """edge-tts was not found on PATH.

Install it (it's separate from whatever Python runs this script):
    uv tool install edge-tts
    pipx install edge-tts
    pip install edge-tts

Requires Python 3.7+. https://pypi.org/project/edge-tts/"""


def find_edge_tts() -> str:
    path = shutil.which("edge-tts")
    if path is None:
        sys.exit(INSTALL_HELP)
    return path


def default_engine() -> str:
    """The engine resources/bootstrap.py last recorded as verified, or edge-tts."""
    if MARKER_PATH.exists():
        return MARKER_PATH.read_text(encoding="utf-8").strip()
    return "edge-tts"


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("input", type=Path, nargs="?", help="Speech-ready .txt file")
    parser.add_argument("-o", "--output", type=Path, default=None,
                         help="Output .mp3 path (default: <input>.mp3 next to the input file)")
    parser.add_argument("--engine", default=None,
                         help="TTS engine to render with (default: whatever resources/bootstrap.py "
                              "last verified, or edge-tts)")
    parser.add_argument("--voice", default=DEFAULT_VOICE)
    parser.add_argument("--rate", default=DEFAULT_RATE)
    parser.add_argument("--list-voices", action="store_true", help="List available edge-tts voices and exit")
    args = parser.parse_args()

    engine = args.engine or default_engine()
    if engine not in WIRED_ENGINES:
        sys.exit(
            f"Engine '{engine}' isn't wired into render.py yet. resources/bootstrap.py can verify "
            "its prerequisites, but this script only renders through edge-tts so far.\n"
            "Pass --engine edge-tts, or contribute rendering support — see CONTRIBUTING.md."
        )

    edge_tts = find_edge_tts()

    if args.list_voices:
        subprocess.run([edge_tts, "--list-voices"], check=True)
        return

    if args.input is None:
        parser.error("input is required unless --list-voices is given")
    if not args.input.exists():
        sys.exit(f"Input file not found: {args.input}")

    output = args.output or args.input.with_suffix(".mp3")
    output.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        edge_tts,
        "--file", str(args.input),
        "--write-media", str(output),
        "--voice", args.voice,
        f"--rate={args.rate}",
    ]

    print("Rendering — this runs slower than real time; a long document can take several minutes.")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        manual_cmd = (
            f'edge-tts --file "{args.input}" --write-media "{output}" '
            f'--voice {args.voice} --rate={args.rate}'
        )
        sys.exit(
            "edge-tts failed to render. This can happen when a sandboxed shell blocks the "
            "network call edge-tts makes (some agent harnesses do this).\n"
            "Run the command yourself in a regular terminal:\n\n"
            f"  {manual_cmd}\n"
        )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
