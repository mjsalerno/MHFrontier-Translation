#!/usr/bin/env python3
"""
Clean up the translations/fr/ tree and bootstrap translations/en/.

Background
----------
The current ``translations/fr/`` CSVs were extracted from a binary that had
already been partially patched by an older English fan-translation effort.
The result: thousands of rows in the ``source`` column contain English text
where Japanese was expected — most visibly in ``pac/text_*`` and
``jmp/menu/*``. Meanwhile every ``target`` is empty, so no actual French
translation has been migrated yet.

This script does two non-destructive things:

1. **Audit**: report per-file how many rows look like JP source, ASCII/English
   source, "dummy"/placeholder source, and identifier-only source
   (e.g. ``Z3P_item_055``, ``wi956``).

2. **Bootstrap ``translations/en/``**: mirror the ``fr/`` directory tree, copy
   every row, and for rows whose ``fr/`` source is ASCII English, populate the
   ``target`` column in ``en/`` with that English text. Source is preserved
   verbatim so a future re-extraction from a clean JP binary can replace it.

The fr/ tree is left untouched. Decisions about whether to drop dummy rows,
re-extract from a clean JP binary, etc. are deferred — see audit output.

Usage::

    python scripts/cleanup.py --audit          # report only
    python scripts/cleanup.py --bootstrap-en   # write translations/en/
    python scripts/cleanup.py                  # both
"""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FR_DIR = ROOT / "translations" / "fr"
EN_DIR = ROOT / "translations" / "en"

JP_RE = re.compile(r"[\u3040-\u30ff\u4e00-\u9fff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z]{2,}")
IDENT_RE = re.compile(r"^[A-Za-z]{1,4}\d+(_\d+)?$")  # wi956, Z3P_item_055
DUMMY_RE = re.compile(r"^(dummy|None|null|\?+)$", re.IGNORECASE)


def classify(source: str) -> str:
    """Return one of: jp, dummy, ident, english, other."""
    s = source.strip()
    if not s:
        return "other"
    if JP_RE.search(s):
        return "jp"
    if DUMMY_RE.match(s):
        return "dummy"
    if IDENT_RE.match(s):
        return "ident"
    if LATIN_WORD_RE.search(s):
        return "english"
    return "other"


def iter_csvs(root: Path):
    return sorted(root.rglob("*.csv"))


def audit() -> dict:
    totals: dict[str, int] = defaultdict(int)
    per_file: dict[str, dict[str, int]] = {}
    for path in iter_csvs(FR_DIR):
        counts: dict[str, int] = defaultdict(int)
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) != 3:
                    continue
                kind = classify(row[1])
                counts[kind] += 1
                totals[kind] += 1
                totals["__total__"] += 1
        per_file[str(path.relative_to(FR_DIR))] = counts
    return {"totals": dict(totals), "per_file": per_file}


def print_audit(report: dict) -> None:
    header = f"{'file':50} {'jp':>7} {'eng':>7} {'dummy':>7} {'ident':>7} {'other':>7}"
    print(header)
    print("-" * len(header))
    for f, c in report["per_file"].items():
        if not any(c.values()):
            continue
        print(
            f"{f:50} "
            f"{c.get('jp', 0):>7} {c.get('english', 0):>7} "
            f"{c.get('dummy', 0):>7} {c.get('ident', 0):>7} {c.get('other', 0):>7}"
        )
    t = report["totals"]
    print("-" * len(header))
    print(
        f"{'TOTAL':50} "
        f"{t.get('jp', 0):>7} {t.get('english', 0):>7} "
        f"{t.get('dummy', 0):>7} {t.get('ident', 0):>7} {t.get('other', 0):>7}"
    )
    print(f"\nGrand total rows: {t.get('__total__', 0)}")


def bootstrap_en() -> int:
    """Mirror fr/ → en/, populating target where fr/ source is English."""
    written = 0
    populated = 0
    for src in iter_csvs(FR_DIR):
        rel = src.relative_to(FR_DIR)
        dst = EN_DIR / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(src, encoding="utf-8", newline="") as fin, \
             open(dst, "w", encoding="utf-8", newline="") as fout:
            reader = csv.reader(fin)
            writer = csv.writer(fout, lineterminator="\n")
            header = next(reader, None)
            if header:
                writer.writerow(header)
            for row in reader:
                if len(row) != 3:
                    writer.writerow(row)
                    continue
                loc, source, _target = row
                if classify(source) == "english":
                    writer.writerow([loc, source, source])
                    populated += 1
                else:
                    writer.writerow([loc, source, ""])
        written += 1
    print(f"Wrote {written} files under {EN_DIR.relative_to(ROOT)}/ "
          f"({populated} pre-populated targets)")
    return populated


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--audit", action="store_true", help="Print classification report")
    p.add_argument("--bootstrap-en", action="store_true",
                   help="Create translations/en/ tree")
    args = p.parse_args()

    do_audit = args.audit or not (args.audit or args.bootstrap_en)
    do_boot = args.bootstrap_en or not (args.audit or args.bootstrap_en)

    if do_audit:
        print_audit(audit())
        print()
    if do_boot:
        bootstrap_en()


if __name__ == "__main__":
    main()
