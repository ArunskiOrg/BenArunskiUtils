# tts

Turns a document into spoken-word MP3 audio. The useful part isn't the MP3 render, it's the rewrite: TTS engines mangle code, symbols, lists, tables, and markdown, so the document is rewritten into speech-friendly prose first, then rendered with a neural TTS engine — [`edge-tts`](https://pypi.org/project/edge-tts/) by default.

## Install as a Claude Code skill

```bash
npx skills add ArunskiOrg/BenArunskiUtils --skill tts -g
```

`-g` installs at the user level; drop it for the current project instead. See the [root README](https://github.com/ArunskiOrg/BenArunskiUtils#30-second-install) for the other options, and the [Claude Code skills docs](https://code.claude.com/docs/en/skills) for where each scope puts the files.

Then ask Claude to convert a document to audio, or say "read this aloud" / mention "text to speech." The first run walks you through `resources/bootstrap.py` to pick and verify a TTS engine (see below); later runs skip straight to converting.

## Requirements and choosing a TTS engine

Python 3.9+ to run the scripts in this folder, plus a verified TTS engine. For the default engine that means `edge-tts` at or above the minimum version, installed and confirmed per the [root README's Prerequisites section](https://github.com/ArunskiOrg/BenArunskiUtils#prerequisites), which names the version and the install and verification commands. The skill's first run walks through `resources/bootstrap.py`, which checks prerequisites and helps pick an engine — free or paid. Later runs skip that step; to change engines, clear the recorded choice with `python3 resources/bootstrap.py --reset` (or ask Claude to run it), and the next run walks through bootstrap again.

`scripts/split_text.py` and `scripts/glue_text.py` are there for the rewrite agents, which use them to chunk and reassemble a document too long for one reply.

Free, local: `edge-tts` (default; cross-platform CLI, no account) and `macos-say` (built in on macOS). Paid, API-key based: `elevenlabs`, `openai-tts`, `azure-speech` — bootstrap verifies the relevant environment variable is set, but doesn't hand you sign-up steps itself; ask Claude (or check the provider's site) for current instructions, since those change over time and this repo won't keep stale copies of them.

Only `edge-tts` is wired into `scripts/render.py` today; bootstrap will tell you if you've verified a different engine that isn't wired up yet — see `CONTRIBUTING.md` to add one. `render.py` itself checks for the engine's CLI before doing anything else and exits with install instructions if it's missing, rather than failing partway through a multi-minute render; if the render call itself fails, it prints the exact command to run yourself in a regular terminal.

**About the default, `edge-tts`:** it's an unofficial client for Microsoft Edge's "Read Aloud" feature, not a public or endorsed Microsoft API — no API key, no SLA. Its [maintainer describes it as meant for personal use](https://github.com/rany2/edge-tts/discussions/261) and warns it "could stop working at any moment," and that commercial use of the underlying service without a paid Azure subscription may run against Microsoft's terms. Its own source is LGPLv3 (MIT for one file); this repo doesn't vendor that code, only shells out to the installed CLI, so that license doesn't extend to this repo — but it's still worth knowing before you build on it. For production or commercial use, pick one of the paid engines above instead.

## Permissions and network egress

**What it executes.** `scripts/render.py` locates `edge-tts` on `PATH` with `shutil.which` and runs it as a subprocess, passing the rewritten text file and the output MP3 path (`edge-tts --file ... --write-media ... --voice ... --rate=...`), plus `edge-tts --list-voices` when you ask for the voice list. That is the only external program any script in this skill runs. `resources/bootstrap.py` runs nothing: it probes `PATH` for `edge-tts` and `say`, checks `platform.system()`, and tests whether `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`, or `AZURE_SPEECH_KEY` are non-empty. It reads each variable only to test whether it is non-empty, and it never prints, logs, stores, or transmits the value it read. `scripts/split_text.py` and `scripts/glue_text.py` run no subprocesses at all.

**Network egress.** The scripts in this folder open no network connections themselves. All egress comes from the `edge-tts` CLI that `render.py` invokes, which sends the rewritten document text to a Microsoft-operated endpoint (the service behind Edge's Read Aloud) and receives the audio back. The document text you convert therefore leaves your machine and goes to Microsoft. That endpoint is outside this repo's control, and `edge-tts` reaches it as an unofficial client: see the "About the default, `edge-tts`" paragraph under [Requirements and choosing a TTS engine](#requirements-and-choosing-a-tts-engine) for the trust boundary that implies. No telemetry, analytics, or update check is sent by anything in this skill.

**Filesystem writes.** Three locations, and no others, when the scripts are run the way `SKILL.md` runs them. First, the `tts-skill` folder under the OS temp directory (`tempfile.gettempdir()`), where the rewrite passes write `<basename>-pass1.txt`, `-pass2.txt`, optionally `-pass3.txt`, and any `<basename>-<tag>-partNN.txt` chunk files from `split_text.py`. Second, the output folder you pick when the skill asks, which receives `<basename>.mp3`; `render.py` creates that folder if it does not exist. Third, the marker file `.bootstrap-verified` next to `SKILL.md` inside the skill folder itself, written by `bootstrap.py --mark-verified` and deleted by `--reset` to record which engine you chose. Nothing outside those three paths is written, and nothing is written to your home directory, shell profiles, or any Claude configuration. Invoked directly with their default flags rather than through the skill, the scripts write beside their input instead: `render.py` writes `<input>.mp3` next to the input file when `--output` is omitted, `split_text.py` writes its chunks into the input file's own directory when `--output-dir` is omitted, and `glue_text.py` writes the glued result next to the chunks it read when `--output` is omitted.

**Reads.** The source document you name, the intermediate files above, `.bootstrap-verified`, and the skill's own instructions and reference files that Claude loads to run it. Nothing else is read.
