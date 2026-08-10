# code-narrator

Turns a pull request, commit, diff, or code excerpt into spoken-word narration. A diff read aloud verbatim is unlistenable, so an LLM writes a script explaining what changed and why first; that script is then rendered to MP3 by the [`tts`](../tts/README.md) skill.

## Install as a Claude Code skill

Copy or symlink this folder into your skills directory, alongside `tts` (this skill calls it by name):

```
cp -r skills/code-narrator ~/.claude/skills/code-narrator
cp -r skills/tts ~/.claude/skills/tts
```

Then ask Claude to narrate a PR, commit, diff, or code file — "read PR 482 to me," "explain this diff out loud."

## Standalone use (no Claude Code)

1. Resolve the source into plain text with the standalone script:
   ```
   python3 scripts/resolve_source.py 482 -o source.txt          # PR number or URL
   python3 scripts/resolve_source.py HEAD~1 -o source.txt       # commit ref
   python3 scripts/resolve_source.py changes.diff -o source.txt # diff/patch file, used as-is
   python3 scripts/resolve_source.py src/app.py:10-40 -o source.txt  # code, optional line range
   ```
2. Feed `source.txt` and `agents/code-describer.md` to any capable LLM chat, asking for the depth you want (overview, walkthrough, or deep — see the prompt). Save its reply as a narration script.
3. Render the narration script with `tts`'s standalone path (see its README).

## Requirements

- Python 3.9+ to run `scripts/resolve_source.py`.
- `git` on `PATH` for commit and diff-file sources.
- `gh` on `PATH`, authenticated, for pull request sources.
- The `tts` skill for the render step.
