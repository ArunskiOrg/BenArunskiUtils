#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Check tts prerequisites and help pick a neural TTS engine.

The skill's SKILL.md calls this once, to let a user pick and verify an engine, then stops calling it —
see --verified below and SKILL.md's bootstrap step.

Usage:
    python3 bootstrap.py --list                    # engines, availability, install commands (JSON)
    python3 bootstrap.py --check ENGINE             # verify one engine is ready now
    python3 bootstrap.py --mark-verified ENGINE      # record ENGINE as the verified choice
    python3 bootstrap.py --verified                  # print the recorded engine; exit 1 if none
    python3 bootstrap.py --reset                      # forget the recorded choice
"""
import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path

MIN_PYTHON = (3, 9)

# The edge-tts release this repo's render path is pinned to. Stated rather than probed:
# bootstrap runs no subprocesses, and `edge-tts --version` is the user-facing check
# (see the root README's Prerequisites section).
MIN_EDGE_TTS = "7.2.8"

# Lives next to SKILL.md, one level up from this resources/ folder, so it
# survives however the skill folder was installed (copy, symlink, git clone).
MARKER_PATH = Path(__file__).resolve().parent.parent / ".bootstrap-verified"

PIP_STYLE_INSTALL = {
    "uv": f'uv tool install "edge-tts>={MIN_EDGE_TTS}"',
    "pipx": f'pipx install "edge-tts>={MIN_EDGE_TTS}"',
    "pip": f'pip install "edge-tts>={MIN_EDGE_TTS}"',
}


def _env_key_present(var_name):
    return lambda: bool(os.environ.get(var_name))


def _macos_say_install(os_name):
    if os_name != "Darwin":
        return None
    return {"builtin": "Already installed — say ships with macOS."}


ENGINES = {
    "edge-tts": {
        "label": "edge-tts — Microsoft Edge neural voices",
        "tier": "free",
        "kind": "cli",
        "check": lambda: shutil.which("edge-tts") is not None,
        "install": lambda os_name: dict(PIP_STYLE_INSTALL),
        "note": (
            "Cross-platform CLI, no account needed. The default this repo is built around. "
            f"Minimum version {MIN_EDGE_TTS}; confirm with `edge-tts --version`. "
            "Unofficial (reverse-engineered from Microsoft Edge, not a public API) — the "
            "maintainer says it's for personal use; see the README before relying on it "
            "commercially."
        ),
    },
    "macos-say": {
        "label": "say — built-in macOS neural voices",
        "tier": "free",
        "kind": "cli",
        "check": lambda: platform.system() == "Darwin" and shutil.which("say") is not None,
        "install": _macos_say_install,
        "note": "macOS only. Not yet wired into scripts/render.py — see CONTRIBUTING.md.",
    },
    "elevenlabs": {
        "label": "ElevenLabs",
        "tier": "paid",
        "kind": "api-key",
        "check": _env_key_present("ELEVENLABS_API_KEY"),
        "install": lambda os_name: None,
        "note": (
            "Needs an ELEVENLABS_API_KEY. Ask the assistant to look up current sign-up "
            "steps — do not rely on stored docs; pricing and flow change. Not yet wired "
            "into scripts/render.py — see CONTRIBUTING.md."
        ),
    },
    "openai-tts": {
        "label": "OpenAI text-to-speech",
        "tier": "paid",
        "kind": "api-key",
        "check": _env_key_present("OPENAI_API_KEY"),
        "install": lambda os_name: None,
        "note": (
            "Needs an OPENAI_API_KEY. Ask the assistant to look up current sign-up steps. "
            "Not yet wired into scripts/render.py — see CONTRIBUTING.md."
        ),
    },
    "azure-speech": {
        "label": "Azure AI Speech",
        "tier": "paid",
        "kind": "api-key",
        "check": _env_key_present("AZURE_SPEECH_KEY"),
        "install": lambda os_name: None,
        "note": (
            "Needs an AZURE_SPEECH_KEY and region. Ask the assistant to look up current "
            "sign-up steps. Not yet wired into scripts/render.py — see CONTRIBUTING.md."
        ),
    },
}


def check_python():
    return sys.version_info[:2] >= MIN_PYTHON


def engine_status(os_name):
    return [
        {
            "id": engine_id,
            "label": engine["label"],
            "tier": engine["tier"],
            "kind": engine["kind"],
            "available": engine["check"](),
            "install": engine["install"](os_name),
            "note": engine["note"],
        }
        for engine_id, engine in ENGINES.items()
    ]


def cmd_list():
    os_name = platform.system()
    report = {
        "python_ok": check_python(),
        "python_version": platform.python_version(),
        "os": os_name,
        "engines": engine_status(os_name),
    }
    print(json.dumps(report, indent=2))


def cmd_check(engine_id):
    engine = ENGINES.get(engine_id)
    if engine is None:
        sys.exit(f"Unknown engine: {engine_id}. Run --list to see valid ids.")
    if engine["check"]():
        print(f"{engine_id}: available")
        return
    install = engine["install"](platform.system())
    if install:
        lines = "\n".join(f"  {name}: {cmd}" for name, cmd in install.items())
        sys.exit(f"{engine_id}: not available.\n{lines}")
    sys.exit(f"{engine_id}: not available.\n  {engine['note']}")


def cmd_mark_verified(engine_id):
    if engine_id not in ENGINES:
        sys.exit(f"Unknown engine: {engine_id}. Run --list to see valid ids.")
    MARKER_PATH.write_text(engine_id, encoding="utf-8")
    print(f"Recorded {engine_id} as the verified engine at {MARKER_PATH}")


def cmd_verified():
    if not MARKER_PATH.exists():
        sys.exit(1)
    print(MARKER_PATH.read_text(encoding="utf-8").strip())


def cmd_reset():
    MARKER_PATH.unlink(missing_ok=True)
    print("Cleared the recorded engine choice.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--list", action="store_true", help="Show engines, availability, install commands as JSON"
    )
    group.add_argument("--check", metavar="ENGINE", help="Verify one engine is ready now")
    group.add_argument("--mark-verified", metavar="ENGINE", help="Record ENGINE as the verified choice")
    group.add_argument("--verified", action="store_true", help="Print the recorded engine; exit 1 if none")
    group.add_argument("--reset", action="store_true", help="Forget the recorded choice")
    args = parser.parse_args()

    if args.list:
        cmd_list()
    elif args.check:
        cmd_check(args.check)
    elif args.mark_verified:
        cmd_mark_verified(args.mark_verified)
    elif args.verified:
        cmd_verified()
    elif args.reset:
        cmd_reset()


if __name__ == "__main__":
    main()
