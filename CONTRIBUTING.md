# Contributing

## Scope

This repo holds public Claude Code skills and small standalone utilities. A skill lives at `skills/<name>/` with a `SKILL.md`, a `README.md`, and any `reference/`, `agents/`, `scripts/`, or `resources/` it needs. Keep new skills self-contained: cross-skill dependencies should be named explicitly in the dependent skill's `SKILL.md` and `README.md` (see `explain-yourself`'s dependency on `tts` for the pattern).

## Adding a TTS engine to `tts`

`skills/tts/resources/bootstrap.py`'s `ENGINES` dict already tracks engines that aren't wired into rendering yet (see its entries' `note` fields). To finish one: add a `render_<engine>` path in `skills/tts/scripts/render.py`, add its id to `WIRED_ENGINES`, and cover it in `tests/test_render.py`. Don't add sign-up prose for API-key engines anywhere in the repo — that's generated at bootstrap time on purpose (see `SKILL.md`'s Bootstrap section), not stored.

## Ground rules

- No machine-specific paths, usernames, or environment assumptions. A skill must work for someone who has never seen this repo before, on macOS, Linux, or Windows.
- Prefer Python for anything beyond a one-line command; keep it in `scripts/` so it's usable standalone, without Claude Code.
- Python 3.9+, no third-party dependencies in `scripts/` beyond what a skill's `README.md` documents as a requirement (e.g. `edge-tts`).
- A script that depends on an external tool checks for it up front and fails with install instructions, not partway through.
- New `.py` files carry a `# SPDX-License-Identifier: MIT` line after the shebang (or as line 1 if there is none).

## Before opening a PR

```
python3 -m venv .venv && .venv/bin/pip install pytest ruff
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest
```

(Windows: `.venv\Scripts\pip`, etc.) Both run in CI on every PR; a red check blocks merge.

If you're changing a skill's behavior, re-run it end to end (via Claude Code or the standalone path) and describe what you verified in the PR description — not just that tests pass.

## Tests

- One assertion's worth of behavior per test; name the test for the scenario, not the input values.
- Parametrize when multiple cases share the same action and differ only in input/expected output; give each case a name via `pytest.param(..., id=...)`.
- Given/When/Then comments in every test body.

## Commit and PR

Small, focused commits. PR description explains what changed and why, not just what.
