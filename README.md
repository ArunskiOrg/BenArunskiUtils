# BenArunskiUtils

Public Claude Code skills and standalone utilities. First up: two skills that turn documents and code changes into spoken-word audio. More skills and utilities will land here over time under the same layout.

## What's here

- [`tts`](skills/tts/) — turns a document into an MP3. Rewrites it into speech-friendly prose first (TTS engines mangle code, symbols, tables, and markdown), then renders with `edge-tts`.
- [`code-narrator`](skills/code-narrator/) — turns a pull request, commit, diff, or code excerpt into spoken narration. A diff read aloud verbatim is unlistenable, so it writes an explanation of the change first, then hands that to `tts`.

## 30-second install

As Claude Code skills:

```
git clone https://github.com/ArunskiOrg/BenArunskiUtils
cp -r BenArunskiUtils/skills/tts BenArunskiUtils/skills/code-narrator ~/.claude/skills/
uv tool install edge-tts   # or: pipx install edge-tts / pip install edge-tts
```

Then ask Claude to read a document aloud, or narrate a PR/commit/diff. Each skill's own README covers standalone use (no Claude Code) and full requirements — see [`skills/tts/README.md`](skills/tts/README.md) and [`skills/code-narrator/README.md`](skills/code-narrator/README.md).

## Layout

```
skills/<name>/SKILL.md       — the skill definition Claude Code loads
skills/<name>/README.md      — what it does, both install paths, requirements
skills/<name>/reference/     — rule docs a skill's agents read (tts only)
skills/<name>/agents/        — prompts for agents a skill spawns
skills/<name>/scripts/       — standalone Python; no Claude Code required
skills/<name>/resources/     — one-time setup: prerequisite checks, engine/credential
                                selection (tts only; see skills/tts/resources/bootstrap.py)
tests/                       — pytest, covering the scripts/ and resources/ across all skills
```

A future skill or utility adds a sibling under `skills/` (or a new top-level folder for something that isn't a skill) without touching this structure.

## Development

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff   # or .venv\Scripts\pip on Windows
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).
