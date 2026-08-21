# Explain yourself!

Turns a code file, directory, pull request, commit, or diff into an explanation shaped to match context: a PR or diff gets a file-by-file walkthrough of what changed and why. A file or directory gets a top-down walkthrough. Exact code shows up only where it has to. With [`tts`](../tts/README.md) installed alongside it, the explanation is spoken aloud by default; without it, you get the same explanation as text.

## Install as a Claude Code skill

Install `tts` alongside it unless you want text-only output; when `tts` is present, explanations are spoken by default, so `--all` (both skills) is the usual choice:

```bash
npx skills add ArunskiOrg/BenArunskiUtils --all -g
```

`-g` installs at the user level; drop it for the current project instead. For this skill alone, `--skill explain-yourself` in place of `--all`. See the [root README](https://github.com/ArunskiOrg/BenArunskiUtils#30-second-install) for the other options.

Then ask Claude to explain a PR, commit, diff, file, or directory: "explain PR 482 to me," "walk me through this directory, I'm new to Terraform," "read this diff to me." You'll be asked where the MP3 should go. Say "text only" (or "just write it") to skip the audio.

## Requirements

- Python 3.9+ to run `scripts/resolve_source.py`. On Windows, invoke it as `python` or `py -3` rather than `python3`.
- `git` on `PATH` for commit and diff-file sources.
- `gh` on `PATH`, authenticated, for pull request sources.
- The `tts` skill, installed as a sibling, for the default spoken output. Without it, explanations are text only.

## Standalone use (no Claude Code)

1. Resolve the source into plain text with the standalone script:
   ```bash
   python3 scripts/resolve_source.py 482 -o source.txt              # PR number or URL
   python3 scripts/resolve_source.py HEAD~1 -o source.txt           # commit ref
   python3 scripts/resolve_source.py changes.diff -o source.txt     # diff/patch file, used as-is
   python3 scripts/resolve_source.py src/app.py:10-40 -o source.txt # code, optional line range
   python3 scripts/resolve_source.py terraform/ -o source.txt       # a directory's immediate files
   ```
   It prints `{"output_path": "...", "kind": "..."}`; `kind` tells you which explanation shape applies next.
2. Feed `source.txt`, `agents/explainer.md`, the `kind` value, and any context about the reader ("I'm a novice in Terraform") to any capable LLM chat. Save its reply.
3. That's it! If you also want audio, render it with `tts`'s standalone path (see its README).
