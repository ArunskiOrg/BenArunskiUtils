#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Resolve a pull request, commit, diff file, directory, or code excerpt into one text blob.

Requires git on PATH for commit sources, and gh (authenticated) for pull request sources.

Usage:
    python3 resolve_source.py <source> -o <output.txt> [--kind pr|commit|diff|code|directory]

<source> is one of:
    a PR number or URL           (e.g. 482, https://github.com/org/repo/pull/482)
    a commit SHA or ref          (e.g. HEAD~1, a1b2c3d)
    a path ending .diff or .patch
    a directory path             (its immediate files only, not subdirectories)
    a code file path, optionally with a line range: path/to/file.py:10-40

Prints one JSON line to stdout on success: {"output_path": "...", "kind": "..."}
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

PR_NUMBER_RE = re.compile(r"(\d+)/?$")
LINE_RANGE_RE = re.compile(r":(\d+)-(\d+)$")


def run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"Command failed: {' '.join(cmd)}\n{result.stderr}")
    return result.stdout


def resolve_pr(source: str) -> str:
    match = PR_NUMBER_RE.search(source)
    if not match:
        sys.exit(f"Could not parse a PR number from: {source}")
    number = match.group(1)
    meta = run(["gh", "pr", "view", number, "--json", "title,body,author,baseRefName,headRefName"])
    diff = run(["gh", "pr", "diff", number])
    return f"{meta}\n\n{diff}"


def resolve_commit(ref: str) -> str:
    stat = run(["git", "show", "--stat", ref])
    full = run(["git", "show", ref])
    return f"{stat}\n\n{full}"


def resolve_diff_file(path: str) -> str:
    return pathlib.Path(path).read_text(encoding="utf-8")


def resolve_code(path_spec: str) -> str:
    match = LINE_RANGE_RE.search(path_spec)
    if match:
        path = path_spec[: match.start()]
        start, end = int(match.group(1)), int(match.group(2))
        lines = pathlib.Path(path).read_text(encoding="utf-8").splitlines()
        return "\n".join(lines[start - 1 : end])
    return pathlib.Path(path_spec).read_text(encoding="utf-8")


def resolve_directory(path: str) -> str:
    directory = pathlib.Path(path)
    files = sorted(p for p in directory.iterdir() if p.is_file())
    if not files:
        sys.exit(f"No files found directly in: {path}")
    parts = []
    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue  # skip binary files
        parts.append(f"===== {file_path.name} =====\n{content}")
    if not parts:
        sys.exit(f"No readable text files found directly in: {path}")
    return "\n\n".join(parts)


def guess_kind(source: str) -> str:
    if source.endswith((".diff", ".patch")):
        return "diff"
    if re.fullmatch(r"\d+", source) or "/pull/" in source:
        return "pr"
    # Strip only a genuine trailing ":START-END" line range, not every colon —
    # a naive split(":")[0] also truncates a Windows drive letter (C:/Users/...).
    path = pathlib.Path(LINE_RANGE_RE.sub("", source))
    if path.is_dir():
        return "directory"
    if path.exists():
        return "code"
    return "commit"


RESOLVERS = {
    "pr": resolve_pr,
    "commit": resolve_commit,
    "diff": resolve_diff_file,
    "code": resolve_code,
    "directory": resolve_directory,
}


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("source")
    parser.add_argument("-o", "--output", type=pathlib.Path, required=True)
    parser.add_argument("--kind", choices=sorted(RESOLVERS), help="Force the source kind instead of guessing")
    args = parser.parse_args()

    kind = args.kind or guess_kind(args.source)
    text = RESOLVERS[kind](args.source)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(text, encoding="utf-8")
    print(json.dumps({"output_path": str(args.output), "kind": kind}))


if __name__ == "__main__":
    main()
