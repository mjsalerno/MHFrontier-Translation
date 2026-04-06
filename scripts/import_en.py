#!/usr/bin/env python3
"""
Import English strings from a FrontierTextHandler --extract-all output dir
into translations/en/, matching against translations/fr/ by hex offset.

Pairing rule: each row in fr/<xpath>.csv has a location like
``0xb9c0a0@mhfdat-jp.bin``. We match the hex part against rows in the
corresponding FTH output file (whose locations look like ``0xb9c0a0@mhfdat.bin``).
The English text — same in both source and target columns of FTH output, since
the binary is fully patched — becomes the en/ target.

Usage::

    python scripts/import_en.py --fth-output ../../tools/FrontierTextHandler/output
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FR_DIR = ROOT / "translations" / "fr"
EN_DIR = ROOT / "translations" / "en"

HEX_RE = re.compile(r"^(0x[0-9a-fA-F]+)")


def hex_key(loc: str) -> str | None:
    m = HEX_RE.match(loc)
    return m.group(1).lower() if m else None


def fr_to_fth_name(rel: Path) -> str:
    """translations/fr/dat/items/name.csv → dat-items-name.csv"""
    parts = list(rel.with_suffix("").parts)
    return "-".join(parts) + ".csv"


def load_fth(path: Path) -> dict[str, str]:
    """Return {hex_key: english_text} from an FTH output CSV."""
    out: dict[str, str] = {}
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        next(reader, None)
        for row in reader:
            if len(row) != 3:
                continue
            k = hex_key(row[0])
            if not k:
                continue
            # Prefer target column; fall back to source.
            text = row[2] if row[2] else row[1]
            out[k] = text
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fth-output", required=True, type=Path,
                   help="Path to FrontierTextHandler/output/")
    args = p.parse_args()

    fth_dir: Path = args.fth_output
    if not fth_dir.is_dir():
        raise SystemExit(f"Not a directory: {fth_dir}")

    total_files = 0
    matched_files = 0
    total_rows = 0
    populated_rows = 0
    missing_files: list[str] = []

    for src in sorted(FR_DIR.rglob("*.csv")):
        rel = src.relative_to(FR_DIR)
        total_files += 1
        fth_name = fr_to_fth_name(rel)
        fth_path = fth_dir / fth_name
        if not fth_path.exists():
            missing_files.append(str(rel))
            continue
        matched_files += 1
        en_map = load_fth(fth_path)

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
                loc, source, _old = row
                total_rows += 1
                k = hex_key(loc)
                target = en_map.get(k or "", "")
                # Skip echoing the source as a "translation" (placeholder rows
                # like "−−−−−−", "dummy", and identifier strings will then
                # naturally end up empty if FTH also returned the same value).
                if target and target == source:
                    target = ""
                if target:
                    populated_rows += 1
                writer.writerow([loc, source, target])

    print(f"Files: {matched_files}/{total_files} matched against FTH output")
    if missing_files:
        print(f"  Unmatched fr/ files (no FTH counterpart): {len(missing_files)}")
        for m in missing_files[:10]:
            print(f"    - {m}")
    print(f"Rows: {populated_rows}/{total_rows} EN targets populated "
          f"({100*populated_rows/total_rows:.1f}%)")


if __name__ == "__main__":
    main()
