# Bootstrap instructions — first run only

Followed by `SKILL.md`'s Bootstrap section when `<SKILL_DIR>/.bootstrap-verified` doesn't exist yet. `<SKILL_DIR>` is the folder containing `SKILL.md`, same as elsewhere in this skill.

1. Run `python3 <SKILL_DIR>/resources/bootstrap.py --list`. It reports the Python version, OS, and every known engine's availability and install command, as JSON.
2. If `edge-tts` already shows `"available": true`, use it: run `python3 <SKILL_DIR>/resources/bootstrap.py --mark-verified edge-tts` and continue — no need to ask, but mention once, briefly, that it's unofficial (see README) and paid alternatives exist for production use.
3. Otherwise ask with AskUserQuestion (single-select, first option default):
   - **Use edge-tts (free, recommended)** — the default this skill is built around; unofficial, see README before commercial use.
   - **See other options** — free and paid neural engines. If they pick "see other options," follow up with a second single-select built from `--list`'s `engines` array (label + tier per option).
4. For a free CLI engine (`edge-tts`, `macos-say`): show the install command(s) `--list` reported, wait for the user to install, then confirm with `python3 <SKILL_DIR>/resources/bootstrap.py --check <engine>`.
5. For a paid, API-key engine (`elevenlabs`, `openai-tts`, `azure-speech`): **do not read setup steps from any file in this repo — none exist, on purpose.** Sign-up flows and pricing change, so use WebSearch to find that provider's current API-key page and write the instructions fresh in your reply; never save them to a file. Once the user has set the corresponding environment variable, confirm with `--check <engine>`.
6. Once `--check` confirms the engine, run `python3 <SKILL_DIR>/resources/bootstrap.py --mark-verified <engine>`. If it's anything other than `edge-tts`, say plainly that `scripts/render.py` only renders through `edge-tts` so far (bootstrap just verifies prerequisites for the others) — see `CONTRIBUTING.md` to add one.
