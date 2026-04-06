# CLAUDE.md

Project-specific guidance for the MHFrontier-Translation repository.

## Project role

Per-section CSV translations of Monster Hunter Frontier text, organized as
`translations/<lang>/<xpath>.csv`. Source data is extracted via
[FrontierTextHandler](../../tools/FrontierTextHandler) (see sibling
`mhfrontier/tools/FrontierTextHandler/CLAUDE.md`).

## Copyright: do not commit raw Japanese source text

The original Japanese strings in the `source` column belong to Capcom. The
copyright risk of redistributing them in this repo is low but real, and worth
keeping deliberate:

- **Avoid bulk-importing JP source text** into commits whenever possible.
  Prefer storing only `location` + `target` once a clean tooling path exists,
  or hashing/eliding the source column.
- **Never paste large blocks of JP text** into issues, PR descriptions, or
  CLAUDE memory.
- The current `translations/fr/` files do contain JP source as a transitional
  measure (needed for human reviewers and for migration). Plan to remove or
  hash the source column before any future bulk re-extraction.

When in doubt, treat JP `source` cells as proprietary and minimize their
footprint.

## Layout

```
translations/
  fr/                 ← French (primary)
  en/                 ← English (bootstrapped from polluted source rows)
scripts/
  validate.py         ← CSV format check
  stats.py            ← coverage report → stats.json
  export_json.py      ← bundle for FrontierTextHandler --merge-json
  migrate.py          ← import a monolithic Weblate CSV
  cleanup.py          ← classify rows, bootstrap translations/en/
```

## Known data quality issues

1. **English-as-source pollution** (~799 rows, mostly `pac/text_*` and
   `jmp/menu/*`): the binary used for extraction had been partially patched by
   an older English fan-translation. The "source" for those offsets is English,
   not Japanese. Re-extract from a clean unpatched JP `mhfdat.bin` to fix.
2. **Dummy rows** (~1,348, mostly `dat/items/source.csv`): literal `dummy`
   strings in the binary. Believed to be unused/unimplemented item slots.
   Cross-reference with the untranslated Wii U build before deciding to drop.
3. **Control-code rows** (~6,643): `<join at=...>` glue and color codes — not
   translatable on their own.

Run `python scripts/cleanup.py --audit` for the current breakdown.

## Workflows

```bash
python scripts/validate.py                       # validate all CSVs
python scripts/stats.py                          # regenerate stats.json
python scripts/cleanup.py --audit                # classify rows
python scripts/cleanup.py --bootstrap-en         # mirror fr/ → en/
python scripts/migrate.py --extracted-dir <FTH-output> \
    --translated <weblate.csv> --lang fr         # import Weblate dump
```
