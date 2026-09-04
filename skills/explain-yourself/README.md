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

- Python 3.9+ to run `scripts/resolve_source.py`.
- `git` on `PATH` for commit sources.
- `gh` on `PATH`, authenticated, for pull request sources.
- The `tts` skill, version 1.0.0 or later, installed as a sibling, for the default spoken output. The dependency is optional: without it, explanations are text only.

## Permissions and network egress

**What it executes.** `scripts/resolve_source.py` is the only script here, and it runs exactly two external programs, both as subprocesses with fixed argument lists. For a pull request source it runs `gh pr view <number> --json title,body,author,baseRefName,headRefName` and `gh pr diff <number>`. For a commit source it runs `git show --stat <ref>` and `git show <ref>`. Both use whatever `gh` and `git` you already have on `PATH`, in the repository you are already standing in, with your existing GitHub credentials as `gh` stores them. The script never reads, copies, or prints a token. Diff and patch files, code files, and directories are read directly with Python; no subprocess is involved for those, so a `.diff` source runs neither `git` nor `gh`.

**Network egress.** The script opens no network connections of its own. The only egress is whatever `gh` performs against GitHub when a pull request source is resolved: `gh` fetches that PR's metadata and diff. `resolve_source.py` sends nothing anywhere else and makes no telemetry or update calls of its own; any traffic beyond the PR fetch is `gh`'s own behavior, including its release-version check. If you choose spoken output, the `tts` skill takes over from there and has its own egress, disclosed in [the `tts` README](../tts/README.md#permissions-and-network-egress): the explanation text is sent to a Microsoft-operated endpoint to be rendered as speech.

**Filesystem writes.** This skill's own scripts write two locations, and no others. First, the `explain-yourself-skill` folder under the OS temp directory (`tempfile.gettempdir()`), which receives `<basename>-source.txt` (the resolved source blob) and `<basename>-explanation.md` (the finished explanation); `resolve_source.py` creates the parent folder of its `-o` path if it does not exist. Second, on the audio path, the output folder you pick when `tts` asks, which receives the MP3. On that path `tts` also writes its own temp folder and marker file, listed in [the `tts` README](../tts/README.md#permissions-and-network-egress). Nothing is cached between runs, and no state is kept in your home directory, shell profiles, or any Claude configuration.

**Reads.** The source you name, whether that is a file, the immediate files in a directory, a `.diff` or `.patch` file, or the `git`/`gh` output for a commit or PR, plus the temp files above. Directory sources read only the immediate files in that folder, not subdirectories, and skip anything that is not valid UTF-8.
