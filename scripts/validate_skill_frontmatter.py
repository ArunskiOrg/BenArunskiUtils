#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate the YAML frontmatter of every skills/*/SKILL.md against the documented schema.

Usage:
    python3 scripts/validate_skill_frontmatter.py [ROOT]

ROOT defaults to the repository root inferred from this script's location. Every
problem found is printed as `path: message`; the exit status is 1 if any file
has a problem and 0 otherwise, so the script works directly as a CI gate.

Constraints enforced (from Anthropic's skill authoring documentation):
  name         required, <= 64 characters, lowercase letters/digits/hyphens only,
               and must not contain "anthropic" or "claude"
  description  required, non-empty, <= 1024 characters, no XML tags

Frontmatter is parsed with yaml.safe_load, which constructs plain Python types
only. yaml.load with the default loader can instantiate arbitrary objects named
in the document, so a hostile SKILL.md would execute code during validation.
"""
import argparse
import re
import sys
from pathlib import Path

import yaml

NAME_MAX = 64
DESCRIPTION_MAX = 1024
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
RESERVED_NAME_SUBSTRINGS = ("anthropic", "claude")
# Matches an opening, closing, or self-closing tag, plus comments and processing
# instructions, so `<!-- ... -->` and `<foo/>` are caught alongside `<foo>`.
XML_TAG_PATTERN = re.compile(r"<[!?/]?[A-Za-z][^>]*>|<!--")
FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)


def extract_frontmatter(text: str) -> str:
    """Return the raw YAML block delimited by the leading `---` fences."""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError("no YAML frontmatter block delimited by '---' at the start of the file")
    return match.group(1)


def parse_frontmatter(text: str) -> dict:
    """Parse a SKILL.md body into its frontmatter mapping."""
    block = extract_frontmatter(text)
    try:
        parsed = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        raise ValueError(f"frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"frontmatter must be a mapping of fields, got {type(parsed).__name__}")
    return parsed


def check_name(value) -> list:
    if value is None:
        return ["'name' is missing"]
    if not isinstance(value, str):
        return [f"'name' must be a string, got {type(value).__name__}"]
    problems = []
    if not value:
        problems.append("'name' is empty")
    if len(value) > NAME_MAX:
        problems.append(f"'name' is {len(value)} characters, over the {NAME_MAX}-character limit")
    if value and not NAME_PATTERN.match(value):
        problems.append(f"'name' must use only lowercase letters, digits, and hyphens: {value!r}")
    for reserved in RESERVED_NAME_SUBSTRINGS:
        if reserved in value.lower():
            problems.append(f"'name' must not contain {reserved!r}: {value!r}")
    return problems


def check_description(value) -> list:
    if value is None:
        return ["'description' is missing"]
    if not isinstance(value, str):
        return [f"'description' must be a string, got {type(value).__name__}"]
    problems = []
    if not value.strip():
        problems.append("'description' is empty")
    if len(value) > DESCRIPTION_MAX:
        problems.append(
            f"'description' is {len(value)} characters, over the {DESCRIPTION_MAX}-character limit"
        )
    found = XML_TAG_PATTERN.search(value)
    if found:
        problems.append(f"'description' must not contain XML tags, found {found.group(0)!r}")
    return problems


def validate_frontmatter(frontmatter: dict) -> list:
    """Return every constraint violation in a parsed frontmatter mapping."""
    return check_name(frontmatter.get("name")) + check_description(frontmatter.get("description"))


def validate_file(path: Path) -> list:
    """Return every problem in one SKILL.md, including parse failures."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot be read: {exc}"]
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        return [str(exc)]
    return validate_frontmatter(frontmatter)


def find_skill_files(root: Path) -> list:
    return sorted(root.glob("skills/*/SKILL.md"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root containing the skills/ directory",
    )
    args = parser.parse_args(argv)

    skill_files = find_skill_files(args.root)
    if not skill_files:
        print(f"No skills/*/SKILL.md found under {args.root}", file=sys.stderr)
        return 1

    failures = 0
    for path in skill_files:
        problems = validate_file(path)
        display = path.relative_to(args.root).as_posix()
        if problems:
            failures += 1
            for problem in problems:
                print(f"{display}: {problem}", file=sys.stderr)
        else:
            print(f"{display}: OK")

    if failures:
        print(f"{failures} of {len(skill_files)} SKILL.md file(s) failed validation", file=sys.stderr)
        return 1
    print(f"{len(skill_files)} SKILL.md file(s) passed validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
