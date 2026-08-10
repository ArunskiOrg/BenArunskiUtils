# BenArunskiUtils

Public Claude Code skills and standalone utilities. First up: a skill that turns a document into spoken-word audio, and one that explains code the way you'd want it explained. More skills and utilities will land here over time under the same layout.

## What's here

- [`tts`](skills/tts/) — turns a document into an MP3. Rewrites it into speech-friendly prose first (TTS engines mangle code, symbols, tables, and markdown), then renders with `edge-tts`.
- [`explain-yourself`](skills/explain-yourself/) — explains a code file, directory, pull request, commit, or diff, matching the explanation to what it's explaining: a file-by-file walkthrough for a PR or diff, a top-down structure-then-details walkthrough for a file or directory. Speaking the result aloud, via `tts`, is optional.

## 30-second install

As Claude Code skills:

```
git clone https://github.com/ArunskiOrg/BenArunskiUtils
cp -r BenArunskiUtils/skills/tts BenArunskiUtils/skills/explain-yourself ~/.claude/skills/
uv tool install edge-tts   # or: pipx install edge-tts / pip install edge-tts
```

Then ask Claude to read a document aloud, or explain a PR/commit/diff/file/directory. Each skill's own README covers standalone use (no Claude Code) and full requirements — see [`skills/tts/README.md`](skills/tts/README.md) and [`skills/explain-yourself/README.md`](skills/explain-yourself/README.md).

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
