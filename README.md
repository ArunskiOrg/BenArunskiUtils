# BenArunskiUtils

[![CI](https://github.com/ArunskiOrg/BenArunskiUtils/actions/workflows/ci.yml/badge.svg)](https://github.com/ArunskiOrg/BenArunskiUtils/actions/workflows/ci.yml)

Public Claude Code skills and standalone utilities. First up: a skill that turns a document into spoken-word audio, and one that explains code the way you'd want it explained. More skills and utilities will land here over time under the same layout.

[Prerequisites](#prerequisites) · [30-second install](#30-second-install) · [Troubleshooting](TROUBLESHOOTING.md) · [Development](#development)

## What's here

- [`tts`](skills/tts/) — turns a document into an MP3. Rewrites it into speech-friendly prose first (TTS engines mangle code, symbols, tables, and markdown), then renders with `edge-tts`.
- [`explain-yourself`](skills/explain-yourself/) — explains a code file, directory, pull request, commit, or diff, matching the explanation to what it's explaining: a file-by-file walkthrough for a PR or diff, a top-down structure-then-details walkthrough for a file or directory. With `tts` installed alongside it, the explanation is spoken aloud by default; without it, text only.

## Prerequisites

The `tts` skill renders audio through `edge-tts`, a separate CLI it shells out to. Install it before the first `tts` run, or that run fails on a missing engine. `explain-yourself` on its own does not need it. Minimum version 7.2.8; pick whichever installer you already have:

```bash
uv tool install "edge-tts>=7.2.8"   # one of these three, not all three
pipx install "edge-tts>=7.2.8"
pip install "edge-tts>=7.2.8"
```

Confirm it worked before invoking the skill through an agent:

```bash
edge-tts --version
```

That prints the installed version; anything 7.2.8 or newer is fine. If the command is not found, the install landed somewhere off your `PATH`, or the shell needs restarting to pick it up. If a `tts` run fails with `edge-tts was not found on PATH.`, see [`edge-tts was not found on PATH.` in TROUBLESHOOTING.md](TROUBLESHOOTING.md#edge-tts-was-not-found-on-path).

Before using `edge-tts` for anything beyond personal work, read [the trust boundary in `skills/tts/README.md`](skills/tts/README.md#requirements-and-choosing-a-tts-engine). Paid engines are listed there too.

## 30-second install

Both skills, at the user level, with the [`skills`](https://github.com/vercel-labs/skills) CLI:

```bash
npx skills add ArunskiOrg/BenArunskiUtils --all -g
uv tool install "edge-tts>=7.2.8"   # for tts only; see Prerequisites above for pipx/pip
```

`--all` takes both skills and installs them for every coding agent the CLI detects; `-g` puts them in your user-level skills directory. Variations, same command otherwise:

- drop `-g` to install into the current project's agent directory instead
- `--skill tts` (or `--skill explain-yourself`) for just one of them
- `--copy` to copy the files rather than symlink them
- `-l` to list what's in the repo without installing anything

`tts`'s first run verifies the engine and records your choice, and other engines are available — see [`skills/tts/README.md`](skills/tts/README.md).

Inside Claude Code, the same two skills install as plugins from this repo's own marketplace, without the `skills` CLI. This installs the skill files only, so `tts` still needs `edge-tts` (or another engine) installed separately, as above:

```
/plugin marketplace add ArunskiOrg/BenArunskiUtils
/plugin install tts@benarunski-utils
/plugin install explain-yourself@benarunski-utils
```

Then ask Claude to read a document aloud, or explain a PR/commit/diff/file/directory. Each skill's own README covers its full requirements — see [`skills/tts/README.md`](skills/tts/README.md) and [`skills/explain-yourself/README.md`](skills/explain-yourself/README.md).

If any of this fails, [TROUBLESHOOTING.md](TROUBLESHOOTING.md) lists the error text for the common cases: a missing `edge-tts`, an `npx skills` run rejected on Node version, and the Windows `python3` and `.venv/Scripts` quirks.

### No Node?

`npx skills add` needs Node, and the `/plugin` route needs Claude Code. Without either, clone this repo and copy the skill folders into your user-level skills directory: `~/.claude/skills/` on macOS and Linux, `%USERPROFILE%\.claude\skills\` on Windows.

bash / zsh:

```bash
git clone https://github.com/ArunskiOrg/BenArunskiUtils.git
mkdir -p ~/.claude/skills
cp -r BenArunskiUtils/skills/tts BenArunskiUtils/skills/explain-yourself ~/.claude/skills/
```

PowerShell:

```powershell
git clone https://github.com/ArunskiOrg/BenArunskiUtils.git
New-Item -ItemType Directory -Force "$env:USERPROFILE/.claude/skills"
Copy-Item -Recurse -Force BenArunskiUtils/skills/tts, BenArunskiUtils/skills/explain-yourself "$env:USERPROFILE/.claude/skills/"
```

Command Prompt:

```bat
git clone https://github.com/ArunskiOrg/BenArunskiUtils.git
xcopy /E /I /Y BenArunskiUtils\skills\tts "%USERPROFILE%\.claude\skills\tts"
xcopy /E /I /Y BenArunskiUtils\skills\explain-yourself "%USERPROFILE%\.claude\skills\explain-yourself"
```

Copy only one folder if you want only one skill. Restart Claude Code afterward so it picks up the new directory. `edge-tts` is still required for `tts`; install it as shown above. To update later, pull in the clone and copy again.

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
tests/                       — pytest, covering the scripts/ and resources/ across all skills, and the eval files in evals/
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

See [`CONTRIBUTING.md`](CONTRIBUTING.md), and [TROUBLESHOOTING.md](TROUBLESHOOTING.md#python3-on-windows-and-venvbin-versus-venvscripts) for the errors these interpreter and venv path differences produce.

## Issues

Issues are triaged within 5 business days. This is a single-maintainer side project, so a first reply may be a question or a triage decision; fixes take longer.

## License

[MIT](LICENSE).
