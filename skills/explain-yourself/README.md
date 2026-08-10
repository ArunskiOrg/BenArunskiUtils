# Explain yourself!

Turns a code file, directory, pull request, commit, or diff into a written explanation shaped to match what it's explaining: a PR or diff gets a file-by-file walkthrough of what changed and why, not a listing of the changed code. A file or directory gets a top-down walkthrough: structure first, then how the pieces interact, then the details that matter. Exact code shows up only where it has to. Speaking the result aloud, via the [`tts`](../tts/README.md) skill, is optional.

## Install as a Claude Code skill

Copy or symlink this folder into your skills directory, alongside `tts` if you want audio output:

```
cp -r skills/explain-yourself ~/.claude/skills/explain-yourself
cp -r skills/tts ~/.claude/skills/tts
```

Then ask Claude to explain a PR, commit, diff, file, or directory: "explain PR 482 to me," "walk me through this directory, I'm new to Terraform," "read this diff to me."

## Standalone use (no Claude Code)

1. Resolve the source into plain text with the standalone script:
   ```
   python3 scripts/resolve_source.py 482 -o source.txt              # PR number or URL
   python3 scripts/resolve_source.py HEAD~1 -o source.txt           # commit ref
   python3 scripts/resolve_source.py changes.diff -o source.txt     # diff/patch file, used as-is
   python3 scripts/resolve_source.py src/app.py:10-40 -o source.txt # code, optional line range
   python3 scripts/resolve_source.py terraform/ -o source.txt       # a directory's immediate files
   ```
   It prints `{"output_path": "...", "kind": "..."}`; `kind` tells you which explanation shape applies next.
2. Feed `source.txt`, `agents/explainer.md`, the `kind` value, and any context about the reader ("I'm a novice in Terraform") to any capable LLM chat. Save its reply.
3. That's the deliverable. If you also want audio, render it with `tts`'s standalone path (see its README).

## Requirements

- Python 3.9+ to run `scripts/resolve_source.py`.
- `git` on `PATH` for commit and diff-file sources.
- `gh` on `PATH`, authenticated, for pull request sources.
- The `tts` skill, only if you want the explanation spoken.
