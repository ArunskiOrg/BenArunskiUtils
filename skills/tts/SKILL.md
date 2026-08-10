---
name: tts
description: Convert a text/markdown document into spoken-word MP3 audio, after rewriting the source into speech-friendly prose (making non-text elements readable aloud). Use when the user asks to convert a document to audio, to read something aloud, mentions TTS or "text to speech", or says to "speak" something. Do NOT auto-engage on bare "say" / "tell me" idioms — those usually want a visual reply; instead ask "btw, do you want mp3 output?" - in that case, only run this skill if they confirm.
---

# tts — document to speech

Turns a document into an MP3: (1) rewrite it into speech-friendly prose, (2) render with a neural TTS engine (`edge-tts` by default). TTS engines mangle code, symbols, lists, and markdown, so the rewrite is where the value is.

## Requirements

- Python 3.9+ to run this skill's own scripts.
- A neural TTS engine, verified once via the bootstrap step below. `edge-tts` is the default this skill is built around; see `resources/bootstrap.py` for other free and paid options.

## Bootstrap

Check whether `<SKILL_DIR>/.bootstrap-verified` exists.

- **If it exists**, an engine is already verified — skip straight to Inputs. (`python3 <SKILL_DIR>/resources/bootstrap.py --verified` prints which one, if you need to mention it.)
- **If it doesn't**, read and follow `<SKILL_DIR>/resources/bootstrap-instructions.md` in full.

## Inputs

1. Confirm the **Source file** — a path passed with the request. If none was given, ask for one. Accept `.md`, `.txt`, or any plain-text file. (For PDFs, extract text first, e.g. with `pdftotext`.)
2. Always ask for **Output folder** with AskUserQuestion (single-select). Options:
   - Current directory
   - Source document's folder — include this option ONLY if it differs from the current directory
   - Other (let the user type a path)

The output filename is `<source-basename>.mp3` in the chosen folder.

## Procedure

The rewrite is token-heavy but mechanical, so it runs in **spawned agents** that write to files and return only a short summary, keeping the primary thread cheap. The primary thread does input-gathering and orchestration; agents do the rewrite in two (sometimes three) passes, each loading only its own rules — the primary thread never opens the rule docs or the source doc.

Path variables used below:
- `<SOURCE>` — the source file path.
- `<basename>` — the source filename without extension.
- `<SKILL_DIR>` — the folder containing this `SKILL.md` (you already know this path — it's wherever you read this file from).
- `<TEMP>` — a `tts-skill` folder under the OS temp directory. Resolve it once with `python3 -c "import tempfile, os; print(os.path.join(tempfile.gettempdir(), 'tts-skill'))"`, then create it if absent. All files UTF-8, no BOM.

1. **Pass 1 — structure and code.** Spawn one agent (`subagent_type: general-purpose`, `model: sonnet`) with prompt: `"Follow <SKILL_DIR>/agents/pass1-structural-rewriter.md. ## Input\n<JSON below>"`, expecting `{"status", "heading_scheme", "doubts"}` back:
   ```json
   {
     "source": "<SOURCE>",
     "rules_reference": "<SKILL_DIR>/reference/preprocessing-rules-1.md",
     "output_path": "<TEMP>/<basename>-pass1.txt",
     "skill_dir": "<SKILL_DIR>",
     "temp": "<TEMP>",
     "basename": "<basename>"
   }
   ```

2. **Pass 2 — token-level sweep.** Same type/model, prompt: `"Follow <SKILL_DIR>/agents/pass2-token-sweep.md. ## Input\n<JSON below>"`, expecting `{"status", "significant_doubts"}` back:
   ```json
   {
     "input_document": "<TEMP>/<basename>-pass1.txt",
     "rules_reference": "<SKILL_DIR>/reference/preprocessing-rules-2.md",
     "output_path": "<TEMP>/<basename>-pass2.txt",
     "skill_dir": "<SKILL_DIR>",
     "temp": "<TEMP>",
     "basename": "<basename>"
   }
   ```

3. **Evaluate doubts (primary thread).** Read Pass 2's returned JSON.
   - `significant_doubts` empty → `<basename>-pass2.txt` is the final edited copy.
   - Non-empty → surface them to the operator as candidate **skill improvements** (so the rules can be tightened), AND spawn a third agent, same type/model, prompt: `"Follow <SKILL_DIR>/agents/pass3-doubt-resolver.md. ## Input\n<JSON below>"`. Its output file, `<TEMP>/<basename>-pass3.txt`, becomes the final edited copy:
     ```json
     {
       "input_document": "<TEMP>/<basename>-pass2.txt",
       "rules_reference_1": "<SKILL_DIR>/reference/preprocessing-rules-1.md",
       "rules_reference_2": "<SKILL_DIR>/reference/preprocessing-rules-2.md",
       "doubts": ["<Pass 2's significant_doubts>"],
       "output_path": "<TEMP>/<basename>-pass3.txt"
     }
     ```

4. **Convert (primary thread).** Warn the user up front: rendering is slower than real time — a long document can take minutes. Run `python3 <SKILL_DIR>/scripts/render.py <final -passN.txt> -o "<output folder>/<basename>.mp3"` and relay its output verbatim: it checks the engine's CLI is installed before starting, and if the render call itself fails (e.g. a sandboxed shell blocking the network call), it prints the exact command for the user to run themselves. Offer `--list-voices` or a different `--rate` if the user wants one.
