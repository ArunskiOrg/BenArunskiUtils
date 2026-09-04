---
name: explain-yourself
description: Explain a code file, directory, pull request, commit, or diff, spoken aloud by default when the tts skill is installed, in writing otherwise. Matches the explanation to what it's explaining, a PR/commit/diff gets a file-by-file walkthrough of what changed and why (not a code listing); a file or directory gets a top-down explanation (structure, then how the pieces interact, then the details that matter), with exact code shown only where necessary. Adapts to stated context like "I'm a novice in Terraform." Use when the user wants a PR/commit/diff/file/directory explained, walked through, or summarized, or wants to listen to one. For a document that's already prose, use the tts skill directly.
version: 1.0.0
---

# Explain yourself! — code and change explanations, written or spoken

Turns a code file, directory, pull request, commit, or diff into an explanation shaped to match what it's explaining, not a transcription of it. The explanation is spoken aloud, via the [`tts`](../tts/SKILL.md) skill, whenever `tts` is installed; without it the same explanation is delivered as text.

## Requirements

- `git` on PATH for commit sources; `gh` on PATH and authenticated for pull request sources.
- Python 3.9+ to run `scripts/resolve_source.py`.
- The `tts` skill, installed as a sibling skill, for the default spoken output (see this repo's root README for the install path). Without it this skill still works, text only.

What this skill executes, sends over the network, and writes to disk is disclosed in [README.md, "Permissions and network egress"](README.md#permissions-and-network-egress).

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
4. **Audio or text** — audio is the default. Check once whether `<SKILL_DIR>/../tts/SKILL.md` exists.
   - It exists: produce audio, unless the request asks for text ("just write it," "don't read it aloud," "text only," "no audio"). Don't ask for an output location here; `tts` asks for its own output folder when you invoke it.
   - It doesn't exist: text only. Say plainly that `tts` isn't installed, so the explanation is written rather than spoken, and point at this repo's root README for installing it.

## Procedure

The source may be large, so the primary thread never reads it directly, and it doesn't read the finished explanation either on the default audio path (step 3). It reads the explanation only when text is the deliverable (step 4).

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
3. **Audio (default, `tts` installed).** Do not open the explanation file. Invoke the `tts` skill with `<TEMP>/<basename>-explanation.md` as its source file. It asks where the MP3 goes and handles the speech rewrite and the render; don't duplicate that prompt here. Report the explanation path; let `tts` report the MP3 path.
4. **Text (`tts` not installed, or text was requested).** Read `<TEMP>/<basename>-explanation.md` and present it to the user directly, it's the deliverable. If `tts` is absent, say so, and that installing it makes spoken output the default.

## Notes

- The explanation can use headings (one per file) and backticked code or identifiers; it isn't "prose only" the way a `tts`-direct source has to be. `tts`'s own rules already convert headings and identifiers for speech when the explanation gets rendered to audio.
- Nothing is cached. Re-running re-resolves the source, which is what you want for a pull request that has moved since the last run.
