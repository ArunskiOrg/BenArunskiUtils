# tts

Turns a document into spoken-word MP3 audio. The useful part isn't the MP3 render, it's the rewrite: TTS engines mangle code, symbols, lists, tables, and markdown, so the document is rewritten into speech-friendly prose first, then rendered with a neural TTS engine — [`edge-tts`](https://pypi.org/project/edge-tts/) by default.

## Install as a Claude Code skill

```bash
npx skills add ArunskiOrg/BenArunskiUtils --skill tts -g
```

`-g` installs at the user level; drop it for the current project instead. See the [root README](https://github.com/ArunskiOrg/BenArunskiUtils#30-second-install) for the other options, and the [Claude Code skills docs](https://code.claude.com/docs/en/skills) for where each scope puts the files.

Then ask Claude to convert a document to audio, or say "read this aloud" / mention "text to speech." The first run walks you through `resources/bootstrap.py` to pick and verify a TTS engine (see below); later runs skip straight to converting.

## Standalone use (no Claude Code)

The rewrite passes are prompt-driven — `reference/preprocessing-rules-1.md` and `reference/preprocessing-rules-2.md` are the full instructions. Feed a document and each rules file to any capable LLM chat in turn (structure pass, then token-level sweep) and save its output.

Once you have a speech-ready `.txt` file, render it with the standalone script — no LLM needed for this step:

```bash
python3 scripts/render.py mydoc.txt -o mydoc.mp3
python3 scripts/render.py --list-voices
```

On Windows, substitute `python` (or `py -3`) for `python3` in this and every other command below.

`scripts/split_text.py` and `scripts/glue_text.py` help an LLM chunk and reassemble a document that's too long for one reply; see their `--help`.

## Requirements and choosing a TTS engine

Python 3.9+ to run the scripts in this folder, plus a verified TTS engine. `resources/bootstrap.py` checks prerequisites and helps pick one — free or paid:

```bash
python3 resources/bootstrap.py --list             # engines, availability, install commands (JSON)
python3 resources/bootstrap.py --check edge-tts    # verify one engine is ready
python3 resources/bootstrap.py --mark-verified edge-tts  # record your choice so future runs skip this step
```

Free, local: `edge-tts` (default; cross-platform CLI, no account) and `macos-say` (built in on macOS). Paid, API-key based: `elevenlabs`, `openai-tts`, `azure-speech` — bootstrap verifies the relevant environment variable is set, but doesn't hand you sign-up steps itself; ask Claude (or check the provider's site) for current instructions, since those change over time and this repo won't keep stale copies of them.

Only `edge-tts` is wired into `scripts/render.py` today; bootstrap will tell you if you've verified a different engine that isn't wired up yet — see `CONTRIBUTING.md` to add one. `render.py` itself checks for the engine's CLI before doing anything else and exits with install instructions if it's missing, rather than failing partway through a multi-minute render; if the render call itself fails, it prints the exact command to run yourself in a regular terminal.

**About the default, `edge-tts`:** it's an unofficial client for Microsoft Edge's "Read Aloud" feature, not a public or endorsed Microsoft API — no API key, no SLA. Its [maintainer describes it as meant for personal use](https://github.com/rany2/edge-tts/discussions/261) and warns it "could stop working at any moment," and that commercial use of the underlying service without a paid Azure subscription may run against Microsoft's terms. Its own source is LGPLv3 (MIT for one file); this repo doesn't vendor that code, only shells out to the installed CLI, so that license doesn't extend to this repo — but it's still worth knowing before you build on it. For production or commercial use, pick one of the paid engines above instead.
