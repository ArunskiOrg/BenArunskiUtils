---
name: code-narrator
description: Turn a code section, pull request, commit, or diff file into spoken-word MP3 audio by first writing a narration script that explains what changed and why, then handing that script to the tts skill. Use when the user wants to listen to a code review, hear what a PR or commit changed, asks to explain a diff out loud, or wants audio produced from code rather than from a prose document. For narrating a document that is already prose, use the tts skill directly.
---

# code-narrator — code to spoken narration

Two stages: a spawned agent reads the source and writes a narration script, then the [`tts`](../tts/SKILL.md) skill renders that script to MP3. The script is where the value is. A diff read aloud verbatim is unlistenable, so the agent explains the change rather than transcribing it.

## Requirements

- The `tts` skill, installed as a sibling skill (see this repo's root README for the install path) — this skill's last step hands off to it.
- `git` on PATH for commit/diff sources; `gh` on PATH and authenticated for pull request sources.
- Python 3.9+ to run `scripts/resolve_source.py`.

## Inputs

1. **Source** — one of, resolved in this order:
   - Pull request: a number (`482`) or URL → `gh pr view <n> --json title,body,author,baseRefName,headRefName` then `gh pr diff <n>`
   - Commit: a SHA or ref → `git show --stat <ref>` then `git show <ref>`
   - Diff file: a path ending `.diff` or `.patch` → used as-is
   - Code: a file path, optionally `path:START-END` for a line range

If the argument is missing or fits more than one form, ask which it is.
2. **Depth** — ask with AskUserQuestion (single-select), first option default:
   - Overview — what changed and why, no file-by-file walk
   - Walkthrough — overview plus each significant file
   - Deep — every hunk, including tests, configuration, and generated files
3. **Output folder** — do not ask. The `tts` skill asks for this in stage two.

## Procedure

The source may be large, so the primary thread never reads it.

Path variables used below:
- `<SOURCE>` — the source argument as given (PR number/URL, commit ref, diff path, or code path).
- `<basename>` — a short name derived from the source, used to name working files.
- `<SKILL_DIR>` — the folder containing this `SKILL.md`.
- `<TEMP>` — a `code-narrator-skill` folder under the OS temp directory. Resolve it once with `python3 -c "import tempfile, os; print(os.path.join(tempfile.gettempdir(), 'code-narrator-skill'))"`, then create it if absent. All files UTF-8, no BOM.

1. Resolve the source: `python3 <SKILL_DIR>/scripts/resolve_source.py <SOURCE> -o <TEMP>/<basename>-source.txt`. The script writes metadata before the diff for pull request and commit sources. Redirect its output to the file; do not read it back.
2. Spawn one agent (`subagent_type: general-purpose`, `model: sonnet`) with prompt: `"Follow <SKILL_DIR>/agents/code-describer.md. ## Input\n<JSON below>"`, expecting `{"output_path", "word_count"}` back — do not open the narration file in the primary thread:
   ```json
   {
     "source_file": "<TEMP>/<basename>-source.txt",
     "depth": "<DEPTH>",
     "output_path": "<TEMP>/<basename>-narration.md"
   }
   ```
3. Invoke the `tts` skill with `<TEMP>/<basename>-narration.md` as its source file. It handles the speech rewrite, the output-folder prompt, and the MP3 render.

Report the narration path; let `tts` report the MP3 path.

## Notes

- `tts` already makes code and symbols readable aloud. This skill's agent writes prose, not code. Code blocks in the narration script mean the agent did it wrong.
- Nothing is cached. Re-running re-resolves the source, which is what you want for a pull request that has moved since the last run.
- `scripts/resolve_source.py` also works standalone, outside Claude Code — see the per-skill README.
