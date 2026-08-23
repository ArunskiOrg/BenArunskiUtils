# SPDX-License-Identifier: MIT
"""Render a WAV file to MP3 by shelling out to ffmpeg.

Fixture for the explain-yourself eval scenario `ey-02`. It is a self-contained subprocess wrapper
with the failure modes that scenario asks the skill to explain: a missing binary, a non-zero exit,
and a hung child process.
"""

import shutil
import subprocess
import sys
from pathlib import Path

FFMPEG_TIMEOUT_SECONDS = 300


class RenderError(RuntimeError):
    """Raised when the encoder is unavailable or fails to produce output."""


def find_ffmpeg():
    """Return the path to ffmpeg, or raise with an install hint if it is absent."""
    found = shutil.which("ffmpeg")
    if found is None:
        raise RenderError(
            "ffmpeg was not found on PATH. Install it (brew install ffmpeg, "
            "apt install ffmpeg, or scoop install ffmpeg) and try again."
        )
    return found


def build_command(ffmpeg, source, target, bitrate):
    """Assemble the argument list. Kept separate so it can be asserted on without running it."""
    return [
        ffmpeg,
        "-nostdin",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-codec:a",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(target),
    ]


def render(source, target, bitrate="128k"):
    """Encode `source` to `target`, returning the target path.

    The child is run without a shell so a path containing spaces or quotes cannot be reinterpreted
    as further arguments.
    """
    source = Path(source)
    target = Path(target)
    if not source.is_file():
        raise RenderError(f"Source file does not exist: {source}")

    command = build_command(find_ffmpeg(), source, target, bitrate)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            timeout=FFMPEG_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        # A timed-out child leaves a truncated file behind; a partial MP3 is worse than none.
        target.unlink(missing_ok=True)
        raise RenderError(f"ffmpeg did not finish within {FFMPEG_TIMEOUT_SECONDS} seconds") from None

    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise RenderError(f"ffmpeg exited {completed.returncode}: {detail}")

    if not target.is_file() or target.stat().st_size == 0:
        raise RenderError(f"ffmpeg reported success but wrote no output to {target}")

    return target


def main(argv):
    if len(argv) not in (3, 4):
        print("usage: render_media.py SOURCE.wav TARGET.mp3 [BITRATE]", file=sys.stderr)
        return 2
    try:
        written = render(argv[1], argv[2], argv[3] if len(argv) == 4 else "128k")
    except RenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(written)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
