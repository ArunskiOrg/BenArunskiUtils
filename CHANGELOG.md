# Changelog

Per-skill version history. Each skill carries a semver `version` in its `SKILL.md` frontmatter and is versioned independently, so a release here names the skill it applies to. [`CONTRIBUTING.md`](CONTRIBUTING.md) states when to bump and what counts as a breaking change.

Dates are ISO 8601. Newest entries first.

## explain-yourself

### 1.0.0 - 2026-08-28

Initial recorded version, covering the skill as already published. No behavior change accompanies the version field.

- Explains a file, directory, pull request, commit, or diff, shaping the explanation to the source kind.
- Speaks the explanation aloud through the `tts` skill when `tts` is installed, and falls back to written output when it is not.
- Adapts to stated audience context, such as a declared unfamiliarity with a language or tool.
- Bundles `scripts/resolve_source.py` to resolve the requested source.

## tts

### 1.0.0 - 2026-08-28

Initial recorded version, covering the skill as already published. No behavior change accompanies the version field.

- Rewrites a text or markdown document into speech-friendly prose, then renders it to MP3.
- Renders with `edge-tts` by default; `resources/bootstrap.py` tracks the other engines and reports each one's availability, with an install command where one exists and a note otherwise.
- Bundles `scripts/render.py` for rendering and `scripts/split_text.py` / `scripts/glue_text.py` for long documents.
