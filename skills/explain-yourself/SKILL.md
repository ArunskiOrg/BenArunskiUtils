---
name: explain-yourself
description: Explain a code file, directory, pull request, commit, or diff, in writing, and read aloud if asked. Matches the explanation to what it's explaining, a PR/commit/diff gets a file-by-file walkthrough of what changed and why (not a code listing); a file or directory gets a top-down explanation (structure, then how the pieces interact, then the details that matter), with exact code shown only where necessary. Adapts to stated context like "I'm a novice in Terraform." Use when the user wants a PR/commit/diff/file/directory explained, walked through, or summarized, or wants to listen to one. For a document that's already prose, use the tts skill directly.
---

# Explain yourself! — code and change explanations, written or spoken

Turns a code file, directory, pull request, commit, or diff into a written explanation shaped to match what it's explaining, not a transcription of it. Speaking the result aloud, via the [`tts`](../tts/SKILL.md) skill, is one thing you can do with that explanation, not the point of it.

## Requirements

- `git` on PATH for commit/diff sources; `gh` on PATH and authenticated for pull request sources.
- Python 3.9+ to run `scripts/resolve_source.py`.
- The `tts` skill, installed as a sibling skill, only if audio output is wanted (see this repo's root README for the install path).

## Inputs

1. **Source** — one of, resolved in this order:
   - Pull request: a number (`482`) or URL
   - Commit: a SHA or ref
   - Diff file: a path ending `.diff` or `.patch`
   - Directory: a folder path — explains its immediate files, not subdirectories
   - Code: a file path, optionally `path:START-END` for a line range

If the argument is missing or fits more than one form, ask which it is.
2. **Context** (optional) — if the request names the reader's background or what to focus on ("I'm a novice in Terraform," "focus on the API layer"), capture it verbatim. Otherwise leave it empty; don't ask for it.
3. **Detail level** — default to `standard` (the full walkthrough) without asking. Only offer a choice, a couple of options, not three, if the request itself signals uncertainty ("not sure how much detail," "just the gist or everything?"): AskUserQuestion (single-select) with **Quick summary** and **Full walkthrough (recommended)**.
4. **Audio or text** — infer from the request's own language: "listen," "hear," "read aloud," "MP3," or similar means audio; otherwise text only. If genuinely ambiguous, default to text and mention that spoken output is available.

## Procedure

The source may be large, so the primary thread never reads it directly, but it does read the finished explanation when the deliverable is text (step 3).

Path variables used below:
- `<SOURCE>` — the source argument as given.
- `<basename>` — a short name derived from the source, used to name working files.
- `<SKILL_DIR>` — the folder containing this `SKILL.md`.
- `<TEMP>` — an `explain-yourself-skill` folder under the OS temp directory. Resolve it once with `python3 -c "import tempfile, os; print(os.path.join(tempfile.gettempdir(), 'explain-yourself-skill'))"`, then create it if absent. All files UTF-8, no BOM.

1. Resolve the source: `python3 <SKILL_DIR>/scripts/resolve_source.py <SOURCE> -o <TEMP>/<basename>-source.txt`. It prints one JSON line, `{"output_path", "kind"}` — read `kind` from it; do not open the resolved source file itself.
2. Spawn one agent (`subagent_type: general-purpose`, `model: sonnet`) with prompt: `"Follow <SKILL_DIR>/agents/explainer.md. ## Input\n<JSON below>"`, expecting `{"output_path", "word_count"}` back:
   ```json
   {
     "source_file": "<TEMP>/<basename>-source.txt",
     "kind": "<kind from step 1>",
     "detail": "<quick | standard | deep, per Inputs step 3>",
     "audience": "<context from Inputs step 2, or empty>",
     "output_path": "<TEMP>/<basename>-explanation.md"
   }
   ```
3. If audio was not requested: read `<TEMP>/<basename>-explanation.md` and present it to the user directly, it's the deliverable. Mention that spoken output is available if they want it.
4. If audio was requested: do not open the explanation file. Invoke the `tts` skill with `<TEMP>/<basename>-explanation.md` as its source file. It handles the speech rewrite, the output-folder prompt, and the MP3 render. Report the explanation path; let `tts` report the MP3 path.

## Notes

- The explanation can use headings (one per file) and backticked code or identifiers; it isn't "prose only" the way a `tts`-direct source has to be. `tts`'s own rules already convert headings and identifiers for speech when the explanation gets rendered to audio.
- Nothing is cached. Re-running re-resolves the source, which is what you want for a pull request that has moved since the last run.
- `scripts/resolve_source.py` also works standalone, outside Claude Code, see the per-skill README.
