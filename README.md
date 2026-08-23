# BenArunskiUtils

[![CI](https://github.com/ArunskiOrg/BenArunskiUtils/actions/workflows/ci.yml/badge.svg)](https://github.com/ArunskiOrg/BenArunskiUtils/actions/workflows/ci.yml)

Public Claude Code skills and standalone utilities. First up: a skill that turns a document into spoken-word audio, and one that explains code the way you'd want it explained. More skills and utilities will land here over time under the same layout.

## What's here

- [`tts`](skills/tts/) — turns a document into an MP3. Rewrites it into speech-friendly prose first (TTS engines mangle code, symbols, tables, and markdown), then renders with `edge-tts`.
- [`explain-yourself`](skills/explain-yourself/) — explains a code file, directory, pull request, commit, or diff, matching the explanation to what it's explaining: a file-by-file walkthrough for a PR or diff, a top-down structure-then-details walkthrough for a file or directory. With `tts` installed alongside it, the explanation is spoken aloud by default; without it, text only.

## 30-second install

Both skills, at the user level, with the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add ArunskiOrg/BenArunskiUtils --all -g
uv tool install edge-tts   # for tts only; or: pipx install edge-tts / pip install edge-tts
```

`--all` takes both skills and installs them for every coding agent the CLI detects; `-g` puts them in your user-level skills directory. Variations, same command otherwise:

- drop `-g` to install into the current project's agent directory instead
- `--skill tts` (or `--skill explain-yourself`) for just one of them
- `--copy` to copy the files rather than symlink them
- `-l` to list what's in the repo without installing anything

`edge-tts` is the default TTS engine `tts` renders with; it isn't needed for `explain-yourself` on its own. `tts`'s first run verifies the engine and records your choice, and other engines are available — see [`skills/tts/README.md`](skills/tts/README.md).

Then ask Claude to read a document aloud, or explain a PR/commit/diff/file/directory. Each skill's own README covers its full requirements — see [`skills/tts/README.md`](skills/tts/README.md) and [`skills/explain-yourself/README.md`](skills/explain-yourself/README.md).

## Layout

```
skills/<name>/SKILL.md       — the skill definition Claude Code loads
skills/<name>/README.md      — what it does, how to install it, requirements
skills/<name>/reference/     — rule docs a skill's agents read (tts only)
skills/<name>/agents/        — prompts for agents a skill spawns
skills/<name>/scripts/       — Python the skill and its agents shell out to
skills/<name>/resources/     — one-time setup: prerequisite checks, engine/credential
                                selection (tts only; see skills/tts/resources/bootstrap.py)
evals/                       — behavioral scenarios testing which skill a phrasing routes to
tests/                       — pytest, covering the scripts/ and resources/ across all skills
```

A future skill or utility adds a sibling under `skills/` (or a new top-level folder for something that isn't a skill) without touching this structure.

## Development

`python3` is the interpreter name on macOS and Linux; on Windows use `python` or `py -3`, since `python3` there often resolves to a Microsoft Store stub that does nothing.

bash / zsh:

```bash
python3 -m venv .venv
.venv/bin/pip install pytest ruff
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
```

PowerShell (Windows venvs put executables in `Scripts`, not `bin`):

```powershell
python -m venv .venv
.venv/Scripts/pip install pytest ruff
.venv/Scripts/python -m pytest
.venv/Scripts/python -m ruff check .
```

Command Prompt:

```bat
python -m venv .venv
.venv\Scripts\pip install pytest ruff
.venv\Scripts\python -m pytest
.venv\Scripts\python -m ruff check .
```

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## License

[MIT](LICENSE).
