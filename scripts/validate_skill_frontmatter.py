#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Validate every skills/*/SKILL.md against the documented authoring constraints.

Usage:
    python3 scripts/validate_skill_frontmatter.py [ROOT]

ROOT defaults to the repository root inferred from this script's location. Every
problem found is printed as `path: message`; the exit status is 1 if any file
has a problem and 0 otherwise, so the script works directly as a CI gate.

Constraints enforced (from Anthropic's skill authoring documentation):
  name         required, <= 64 characters, lowercase letters/digits/hyphens only,
               and must not contain "anthropic" or "claude"
  description  required, non-empty, <= 1024 characters, no XML tags
  body         <= 500 lines after the frontmatter block
  references   every markdown file reachable by markdown links from a SKILL.md
               sits at most one hop away from it

The body and reference limits bound what an agent has to load before it can act:
a long body is read in full on every invocation, and a reference more than one
hop away is only found after reading an intermediate file whose only purpose is
to point further.

Frontmatter is parsed with yaml.safe_load, which constructs plain Python types
only. yaml.load with the default loader can instantiate arbitrary objects named
in the document, so a hostile SKILL.md would execute code during validation.
"""
import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import yaml

NAME_MAX = 64
DESCRIPTION_MAX = 1024
BODY_MAX_LINES = 500
REFERENCE_MAX_HOPS = 1
NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")
RESERVED_NAME_SUBSTRINGS = ("anthropic", "claude")
# Matches an opening, closing, or self-closing tag, so `</foo>` and `<foo/>` are
# caught alongside `<foo>`.
XML_TAG_PATTERN = re.compile(r"<[?/]?[A-Za-z][^>]*>")
FRONTMATTER_PATTERN = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
# Inline markdown link, capturing the target up to the first whitespace so a
# title (`[a](b.md "t")`) is dropped. Angle-bracket targets are unwrapped.
MARKDOWN_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)")
# A target starting with a scheme (`https:`, `mailto:`) or `//` addresses
# something outside the repository. A Windows drive letter matches the same
# shape, which is the wanted result: an absolute machine path is not a
# reference another checkout of this repository could follow.
EXTERNAL_TARGET_PATTERN = re.compile(r"\A(?:[A-Za-z][A-Za-z0-9+.-]*:|//)")
MARKDOWN_SUFFIXES = (".md", ".markdown")


def extract_frontmatter(text: str) -> str:
    """Return the raw YAML block delimited by the leading `---` fences."""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError("no YAML frontmatter block delimited by '---' at the start of the file")
    return match.group(1)


def extract_body(text: str) -> str:
    """Return everything after the frontmatter block."""
    match = FRONTMATTER_PATTERN.match(text)
    if not match:
        raise ValueError("no YAML frontmatter block delimited by '---' at the start of the file")
    return text[match.end() :]


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


def check_name(value: object) -> list[str]:
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


def check_description(value: object) -> list[str]:
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


def check_body_length(body: str) -> list[str]:
    lines = len(body.splitlines())
    if lines > BODY_MAX_LINES:
        return [f"body is {lines} lines, over the {BODY_MAX_LINES}-line limit"]
    return []


def markdown_links(path: Path) -> list[Path]:
    """Return the local markdown files linked from one file, resolved against its folder."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return []
    targets = []
    for target in MARKDOWN_LINK_PATTERN.findall(text):
        target = target.split("#", 1)[0]
        if not target or EXTERNAL_TARGET_PATTERN.match(target):
            continue
        if not target.lower().endswith(MARKDOWN_SUFFIXES):
            continue
        resolved = (path.parent / target).resolve()
        # A link to a file that is not there says nothing about how deep the
        # reference tree is, so link integrity is left to a separate check.
        if resolved.is_file():
            targets.append(resolved)
    return sorted(set(targets))


def check_reference_depth(path: Path) -> list[str]:
    """Return a problem for every markdown file sitting more than one hop from a SKILL.md.

    Only files under the skill's own folder are followed. A link that leaves the
    folder points into another skill, which owns its own reference tree and is
    validated on its own terms.
    """
    skill_dir = path.parent.resolve()
    problems = []
    seen = {path.resolve()}
    queue = [(path.resolve(), [])]
    while queue:
        current, chain = queue.pop(0)
        if len(chain) > REFERENCE_MAX_HOPS:
            problems.append(
                f"reference chain runs {len(chain)} hops from SKILL.md, "
                f"over the {REFERENCE_MAX_HOPS}-hop limit: {' -> '.join(chain)}"
            )
            continue
        for target in markdown_links(current):
            if target in seen:
                continue
            if skill_dir not in target.parents:
                continue
            seen.add(target)
            queue.append((target, chain + [target.relative_to(skill_dir).as_posix()]))
    return problems


def validate_frontmatter(frontmatter: dict) -> list[str]:
    """Return every constraint violation in a parsed frontmatter mapping."""
    return check_name(frontmatter.get("name")) + check_description(frontmatter.get("description"))


def validate_file(path: Path) -> list[str]:
    """Return every problem in one SKILL.md, including parse failures."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot be read: {exc}"]
    try:
        frontmatter = parse_frontmatter(text)
    except ValueError as exc:
        # Without a readable frontmatter block the body has no start, so the
        # remaining checks have nothing dependable to measure.
        return [str(exc)]
    return (
        validate_frontmatter(frontmatter)
        + check_body_length(extract_body(text))
        + check_reference_depth(path)
    )


def find_skill_files(root: Path) -> list[Path]:
    return sorted(root.glob("skills/*/SKILL.md"))


def main(argv: Optional[Sequence[str]] = None) -> int:
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
