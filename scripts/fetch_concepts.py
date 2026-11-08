#!/usr/bin/env python3
"""Fetch the daily pageview series for the WAR / PEACE concept baskets.

Output: ``data/generated/concepts_daily.csv.gz`` with columns
    date,lang,family,concept,views

Run from the repository root:  ./.venv/bin/python scripts/fetch_concepts.py
"""

import csv
import gzip
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src import config, pageviews, seeds  # noqa: E402


def main() -> int:
    out_dir = config.DATA / "generated"
    out_dir.mkdir(parents=True, exist_ok=True)

    print("[seeds] resolving concept titles via langlinks ...", flush=True)
    seed_rows = seeds.concept_seed_table()
    resolved = [r for r in seed_rows if r["article"]]
    print(
        "[seeds] %d concept/language pairs, %d resolved to an article"
        % (len(seed_rows), len(resolved)),
        flush=True,
    )

    tasks = [
        (r["lang"], r["article"], config.DATE_START, config.DATE_END) for r in resolved
    ]
    print("[fetch] %d series ..." % len(tasks), flush=True)
    fetched = pageviews.fetch_many(tasks)

    errors = [(k, v["_error"]) for k, v in fetched.items() if "_error" in v]
    empty = [k for k, v in fetched.items() if not v or "_error" in v]
    print("[fetch] ok=%d empty=%d errors=%d" % (len(fetched) - len(empty), len(empty), len(errors)), flush=True)
    for key, err in errors[:5]:
        print("   !", key, err, flush=True)

    out_path = out_dir / "concepts_daily.csv.gz"
    n_rows = 0
    with gzip.open(out_path, "wt", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["date", "lang", "family", "concept", "views"])
        for row in resolved:
            key = (row["lang"], row["article"], config.DATE_START, config.DATE_END)
            series = fetched.get(key, {})
            for date in sorted(series):
                writer.writerow([date, row["lang"], row["family"], row["concept"], series[date]])
                n_rows += 1

    print("[write] %s  (%d rows)" % (out_path.relative_to(ROOT), n_rows), flush=True)
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
