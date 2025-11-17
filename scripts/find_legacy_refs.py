#!/usr/bin/env python3
"""Small utility to search repository for legacy entry script references.

This script looks for references to `AiDupeRanger.py`, `AiDupeRanger_grok`,
`AiDupeRanger_claude`, and other deprecated names and prints any occurrences
outside the `deprecated_variants` directory.

Exit code: 0 = no legacy references found (outside allowed locations)
           1 = legacy references found.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(__file__))
PATTERNS = [r"AiDupeRanger(\.py|_grok|_claude|_clau.*)", r"AiDupeRanger\b"]
EXCLUDE_DIRS = {
    "deprecated_variants",
    ".git",
    ".github",
    "build",
    "dist",
    "AiDupeRanger_grok",
    "AiDupeRanger_claude",
    "AiDupeRanger",
    "DupeRangerAi_2025-11-11",
}


def matches(filename, text):
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            return True
    return False


def main():
    found = []
    for root, dirs, files in os.walk(ROOT):
        # Normalize relative to repo root
        relroot = os.path.relpath(root, ROOT)
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in relroot.split(os.sep) if part):
            continue
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as fh:
                    txt = fh.read()
            except OSError:
                continue
            if matches(fname, txt):
                found.append((os.path.relpath(fpath, ROOT), 1))

    if found:
        print("Found legacy references outside `deprecated_variants`:")
        for p, _ in found:
            print(" - ", p)
        print(
            "\nTip: Put legacy directories and files into `deprecated_variants/` or update references to `DupeRangerAi.py` to canonicalize."
        )
        return 1

    print("No legacy references found outside `deprecated_variants`. Good job!")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
