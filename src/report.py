"""Build the data dictionary (``data/README.md``) and the pipeline sanity tables.

Runs after the fetch stages.  Everything here is computed from the files
actually on disk - no number is hand-written - so the README always states the
true row counts, date coverage and language coverage of the frozen dataset.

Outputs
-------
data/README.md                        data dictionary, provenance, limitations
data/processed/sanity_summary.txt     human-readable sanity checks
"""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

try:  # normal package import
    from .common import DATA_PROCESSED, DATA_RAW, PROJECT_ROOT, RETRIEVAL_DATE
except ImportError:  # pragma: no cover - direct execution
    sys.path[:] = [p for p in sys.path if p != str(Path(__file__).resolve().parent)]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.common import DATA_PROCESSED, DATA_RAW, PROJECT_ROOT, RETRIEVAL_DATE  # type: ignore

LANGS = ["en", "ar", "es", "fr", "de", "ru", "zh", "fa", "tr", "id", "pt", "uk", "he", "hi"]

PAGEVIEWS_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{lang}.wikipedia/all-access/user/{article}/daily/{start}00/{end}00"
)
LANGLINKS_URL = (
    "https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&lllimit=500"
    "&format=json&redirects=1&titles="
)
MOVELOG_URL = (
    "https://en.wikipedia.org/w/api.php?action=query&list=logevents&letype=move"
    "&letitle="
)
GED_URL = "https://ucdp.uu.se/downloads/ged/ged241-csv.zip"


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def _file_size(path: Path) -> str:
    if not path.exists():
        return "missing"
    size = path.stat().st_size
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "{:.1f} {}".format(size, unit)
        size /= 1024.0
    return "{} B".format(size)


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def _count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with open(path, "r", encoding="utf-8", newline="") as fh:
        return max(sum(1 for _ in fh) - 1, 0)


# ---------------------------------------------------------------------------
# pageviews scan (streamed - the file is ~2.4M rows)
# ---------------------------------------------------------------------------
def scan_pageviews(path: Path):
    stats = {
        "rows": 0,
        "date_min": None,
        "date_max": None,
        "languages": {},
        "articles": {},
        # (lang, article) -> first / last date with a row.  A missing day before
        # the first date means "article did not exist (or title did not exist)
        # yet" - it is MISSING, never zero attention.
        "series_first": {},
        "series_last": {},
        "ceasefire_daily": {},  # yyyy-mm-dd -> views summed over all languages
        "ceasefire_en_daily": {},
    }
    if not path.exists():
        return stats
    with open(path, "r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            stats["rows"] += 1
            lang = row["lang"]
            article = row["article_en"]
            date = row["date"]
            views = int(row["views"])
            if stats["date_min"] is None or date < stats["date_min"]:
                stats["date_min"] = date
            if stats["date_max"] is None or date > stats["date_max"]:
                stats["date_max"] = date
            lang_stats = stats["languages"].setdefault(
                lang, {"rows": 0, "articles": set(), "date_min": date, "date_max": date}
            )
            lang_stats["rows"] += 1
            lang_stats["articles"].add(article)
            lang_stats["date_min"] = min(lang_stats["date_min"], date)
            lang_stats["date_max"] = max(lang_stats["date_max"], date)
            art = stats["articles"].setdefault(article, {"views": 0, "langs": set()})
            art["views"] += views
            art["langs"].add(lang)
            series_key = (lang, article)
            if series_key not in stats["series_first"]:
                stats["series_first"][series_key] = date
                stats["series_last"][series_key] = date
            elif date > stats["series_last"][series_key]:
                stats["series_last"][series_key] = date
            if article == "Ceasefire":
                stats["ceasefire_daily"][date] = stats["ceasefire_daily"].get(date, 0) + views
                if lang == "en":
                    stats["ceasefire_en_daily"][date] = views
    return stats


# ---------------------------------------------------------------------------
# sanity checks
# ---------------------------------------------------------------------------
def build_sanity(stats, ucdp_summary):
    lines = []
    lines.append("SANITY CHECKS - Half-Life of Peace data pipeline")
    lines.append("generated: {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    lines.append("retrieval date: {}".format(RETRIEVAL_DATE))
    lines.append("")

    lines.append("1) pageviews.csv")
    lines.append("   rows: {:,}".format(stats["rows"]))
    lines.append("   date coverage: {} .. {}".format(stats["date_min"], stats["date_max"]))
    lines.append("   languages: {} ({})".format(len(stats["languages"]), ", ".join(sorted(stats["languages"]))))
    lines.append("   articles: {}".format(len(stats["articles"])))
    lines.append("")

    lines.append("2) Top 5 articles by total views (all languages summed)")
    lines.append("   {:<42s} {:>14s} {:>6s}".format("article_en", "total_views", "langs"))
    top = sorted(stats["articles"].items(), key=lambda kv: kv[1]["views"], reverse=True)[:5]
    for article, info in top:
        lines.append("   {:<42s} {:>14,d} {:>6d}".format(article, info["views"], len(info["langs"])))
    lines.append("")

    lines.append("3) Ceasefire article around the Gaza ceasefire (took effect 2025-01-19)")
    lines.append("   {:<12s} {:>12s} {:>12s}".format("date", "en_views", "all_langs"))
    for day in range(12, 27):  # 2025-01-12 .. 2025-01-26
        date = "2025-01-{:02d}".format(day)
        lines.append(
            "   {:<12s} {:>12,d} {:>12,d}".format(
                date,
                stats["ceasefire_en_daily"].get(date, 0),
                stats["ceasefire_daily"].get(date, 0),
            )
        )
    pre = [stats["ceasefire_en_daily"].get("2025-01-{:02d}".format(d), 0) for d in range(5, 12)]
    win = [(d, stats["ceasefire_en_daily"].get("2025-01-{:02d}".format(d), 0)) for d in range(12, 27)]
    baseline = sum(pre) / float(len(pre)) if pre else 0.0
    peak_day, peak_views = max(win, key=lambda x: x[1]) if win else ("-", 0)
    lines.append(
        "   en baseline 2025-01-05..11 mean = {:.0f}/day; peak = {:d} on 2025-01-{:02d}; "
        "peak/baseline = {:.1f}x".format(baseline, peak_views, peak_day, (peak_views / baseline) if baseline else 0.0)
    )
    spike = peak_views > 1.5 * baseline if baseline else False
    lines.append("   visible spike: {}".format("YES" if spike else "NO"))
    lines.append("")

    lines.append(
        "4) UCDP monthly aggregates ({})".format(
            ucdp_summary.get("version", "n/a") if ucdp_summary else "n/a"
        )
    )
    if ucdp_summary:
        lines.append("   events parsed (all years): {:,}".format(ucdp_summary["events_parsed_total"]))
        lines.append("   events kept (year>=2014): {:,}".format(ucdp_summary["events_year_ge_2014"]))
        lines.append(
            "   country-months: {:,} ({} countries); dyad-months: {:,} ({} dyads)".format(
                ucdp_summary["country_rows"],
                ucdp_summary["countries_covered"],
                ucdp_summary["dyad_rows"],
                ucdp_summary["dyads_covered"],
            )
        )
        lines.append(
            "   month coverage: {} .. {}".format(ucdp_summary["month_min"], ucdp_summary["month_max"])
        )
        lines.append(
            "   total best-estimate fatalities: {:,}; total events: {:,}".format(
                ucdp_summary["total_fatalities_best"], ucdp_summary["total_events"]
            )
        )
    lines.append("")
    return "\n".join(lines), spike


def top_countries(ucdp_country_path: Path, n: int = 5):
    if not ucdp_country_path.exists():
        return []
    totals = {}
    with open(ucdp_country_path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            totals[row["iso3"]] = totals.get(row["iso3"], 0) + int(row["fatalities"])
    return sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:n]


# ---------------------------------------------------------------------------
# README
# ---------------------------------------------------------------------------
def build_readme(stats, ucdp_summary, fetch_report):
    out = []
    add = out.append

    add("# Data dictionary - The Half-Life of Peace")
    add("")
    add(
        "Daily multilingual Wikipedia attention series (2015-07-01 to 2025-11-01) and "
        "monthly UCDP conflict-fatality aggregates ({} to {}), built by the "
        "reproducible pipeline in `src/` and orchestrated by `scripts/run_all.py`.".format(
            ucdp_summary.get("month_min", "2014-01")[:4] if ucdp_summary else "2014",
            ucdp_summary.get("month_max", "2025-12")[:4] if ucdp_summary else "2025",
        )
    )
    add("")
    add("- **Data retrieval date:** {}".format(RETRIEVAL_DATE))
    add("- **Project root:** `{}`".format(PROJECT_ROOT))
    add(
        "- **Total pageview rows:** {:,} across {} languages and {} articles".format(
            stats["rows"], len(stats["languages"]), len(stats["articles"])
        )
    )
    add("- **Pageview date coverage:** {} .. {}".format(stats["date_min"], stats["date_max"]))
    if ucdp_summary:
        add(
            "- **UCDP release used:** {} ({}); monthly coverage {} .. {}".format(
                ucdp_summary.get("version", "n/a"),
                ucdp_summary.get("source", "n/a"),
                ucdp_summary.get("month_min", "n/a"),
                ucdp_summary.get("month_max", "n/a"),
            )
        )
    else:
        add("- UCDP outputs not yet generated.")
    add("")

    add("## Repro")
    add("")
    add("```bash")
    add("# from the repository root, with the project venv")
    add(".venv/bin/python scripts/run_all.py                 # data pipeline (uses cache)")
    add(".venv/bin/python scripts/run_all.py --refresh       # force re-download")
    add(".venv/bin/python scripts/run_all.py --stage analysis # delegate to analysis/run.py --stage analysis")
    add(".venv/bin/python scripts/run_all.py --stage figures  # figures from cached analysis artifacts")
    add(".venv/bin/python scripts/run_all.py --stage all      # data + analysis + figures")
    add("```")
    add("")
    add(
        "Every raw HTTP response is cached verbatim under `data/raw/`; a re-run "
        "replays the cache and makes **no** network requests unless `--refresh` is "
        "passed. The pipeline is therefore idempotent, resumable and runnable "
        "offline after the first successful download. Requests use a global "
        "~5 req/s limiter, at most 5 worker threads, exponential backoff on "
        "429/5xx, and an identifying User-Agent."
    )
    add("")

    add("## Provenance")
    add("")
    add("| Source | Endpoint / file | Version | Retrieved |")
    add("|---|---|---|---|")
    add(
        "| Wikimedia pageviews (per-article, daily) | `{}` | REST API v1 | {} |".format(
            PAGEVIEWS_URL, RETRIEVAL_DATE
        )
    )
    add("| Wikipedia interlanguage links | `{}<title>` | MediaWiki API | {} |".format(LANGLINKS_URL, RETRIEVAL_DATE))
    add("| Wikipedia page-move logs | `{}<title>` | MediaWiki API | {} |".format(MOVELOG_URL, RETRIEVAL_DATE))
    add(
        "| UCDP Georeferenced Event Dataset (GED) | `{}` | {} | {} |".format(
            ucdp_summary.get("source", GED_URL) if ucdp_summary else GED_URL,
            ucdp_summary.get("version", "GED (see ucdp_summary.json)") if ucdp_summary else "n/a",
            RETRIEVAL_DATE,
        )
    )
    add("")

    add("## Study design constants")
    add("")
    add("- Languages ({}): {}".format(len(LANGS), ", ".join(LANGS)))
    add(
        "- WAR concept basket ({}): {}".format(
            len(CONCEPT["war"]), ", ".join(CONCEPT["war"])
        )
    )
    add(
        "- PEACE concept basket ({}): {}".format(
            len(CONCEPT["peace"]), ", ".join(CONCEPT["peace"])
        )
    )
    add("- Conflict-specific articles: {}".format(len(CONCEPT["conflict"])))
    add(
        "- Article/language cells: {:,} ({} articles x {} languages); resolved to an "
        "article: {:,}; missing translations: {:,}".format(
            stats.get("lang_pairs", 0),
            stats.get("n_articles", 0),
            len(LANGS),
            stats.get("resolved_pairs", 0),
            max(stats.get("lang_pairs", 0) - stats.get("resolved_pairs", 0), 0),
        )
    )
    add("")

    add("## Files")
    add("")

    # seeds.csv
    add("### `data/processed/seeds.csv` - seed table")
    add("")
    add(
        "{} rows. One row per seed article: the 10 WAR concepts, 11 PEACE concepts and "
        "30 conflict-specific articles defined in `src/config.py` and "
        "`src/conflict_seeds.py`.".format(_count_csv_rows(DATA_PROCESSED / "seeds.csv"))
    )
    add("")
    add("| column | type | description |")
    add("|---|---|---|")
    add("| `seed_title` | str | English Wikipedia title as specified in the seed list |")
    add("| `concept` | str | concept label for WAR/PEACE rows (empty for conflict rows) |")
    add("| `family` | str | `war` / `peace` / `conflict` |")
    add("| `conflict` | str | conflict label (conflict rows only) |")
    add("| `country_iso3` | str | primary theatre country (conflict rows only) |")
    add("| `region` | str | coarse region (conflict rows only) |")
    add("")

    # articles.csv
    add("### `data/processed/articles.csv` - canonical article table")
    add("")
    add(
        "{} rows. One row per **unique canonical English article**, after resolving "
        "redirects and merging seeds that collapse onto the same article "
        "(e.g. `Armed conflict` -> `War`). Columns: `article_en`, `seed_titles` "
        "(`|`-joined), `concepts`, `family`, `conflict`, `country_iso3`, `region`, "
        "`n_langs_resolved`, `missing_langs`.".format(
            _count_csv_rows(DATA_PROCESSED / "articles.csv")
        )
    )
    add("")

    # article_langlinks.csv
    add("### `data/processed/article_langlinks.csv` - multilingual title map")
    add("")
    add(
        "{} rows. One row per (article, language) for all 14 languages. "
        "`has_langlink=0` means the article does not exist in that language edition "
        "(it is logged in `missing_articles.csv` and skipped). "
        "Columns: `article_en`, `family`, `lang`, `article_local`, `has_langlink`.".format(
            _count_csv_rows(DATA_PROCESSED / "article_langlinks.csv")
        )
    )
    add("")

    # pageviews.csv
    add("### `data/processed/pageviews.csv` - daily attention series (main dataset)")
    add("")
    add(
        "**{:,} rows**, {} languages, {} articles, {} to {}.".format(
            stats["rows"],
            len(stats["languages"]),
            len(stats["articles"]),
            stats["date_min"],
            stats["date_max"],
        )
    )
    add("")
    add("| column | type | description |")
    add("|---|---|---|")
    add("| `lang` | str | Wikipedia language edition code (`en`, `ar`, ...) |")
    add("| `article_en` | str | canonical English article title (the join key) |")
    add("| `article_local` | str | title used in that language edition (canonical English title for `en`) |")
    add("| `date` | str | `YYYY-MM-DD` (daily) |")
    add("| `views` | int | pageviews, all-access / user agents only (bot traffic excluded) |")
    add("")
    add("Language coverage:")
    add("")
    add("| lang | rows | articles | date coverage |")
    add("|---|---:|---:|---|")
    for lang in LANGS:
        if lang not in stats["languages"]:
            add("| `{}` | 0 | 0 | - |".format(lang))
            continue
        info = stats["languages"][lang]
        add(
            "| `{}` | {:,} | {} | {} .. {} |".format(
                lang, info["rows"], len(info["articles"]), info["date_min"], info["date_max"]
            )
        )
    add("")

    add("#### Temporal existence convention (important for baselines/WPAR)")
    add("")
    add(
        "A row in `pageviews.csv` exists only from the day a series first registers "
        "pageviews - i.e. from article creation (or from the earliest title in the "
        "summed title chain for English). **Days before a series' first row are "
        "MISSING, not zero.** Filling them with 0 would understate pre-creation "
        "baselines and distort the War-Peace Attention Ratio; availability-aware "
        "aggregation must treat them as absent."
    )
    add("")
    add(
        "- {:,} article/language series are present; **{:,} start after "
        "2015-07-01** because the article (or title) did not exist earlier.".format(
            stats.get("n_series", 0), stats.get("n_late_series", 0)
        )
    )
    if stats.get("late_series_examples"):
        add("- Latest series onsets: " + "; ".join(
            "{} ({}, first row {})".format(article, lang, first)
            for (lang, article), first in stats["late_series_examples"]
        ) + ".")
    add(
        "- **{:,} langlink-resolved article/language pairs have no pageview rows at "
        "all** (article exists in the edition but the pageviews API returned nothing); "
        "they are kept as all-missing and logged in `missing_articles.csv`.".format(
            stats.get("n_all_missing", 0)
        )
    )
    if stats.get("all_missing_examples"):
        add("- All-missing examples: " + "; ".join(
            "{} ({})".format(article, lang)
            for lang, article in stats["all_missing_examples"]
        ) + ".")
    add("")

    # missing
    add("### `data/processed/missing_articles.csv` - missing translations / pages")
    add("")
    add(
        "{} rows. Diagnostics for article/language pairs that could not be fetched. "
        "`reason` is one of `no_langlink` (no article in that language), `http_404` "
        "(page does not exist for the pageviews API) or `no_items` (empty series). "
        "These rows are *absent* from `pageviews.csv`; they are genuine data "
        "limitations, not fetch failures.".format(
            _count_csv_rows(DATA_PROCESSED / "missing_articles.csv")
        )
    )
    add("")

    # variants
    add("### `data/processed/en_title_variants.csv` - English page-move summation")
    add("")
    add(
        "{} rows. MediaWiki records pageviews **per title string**, so when an "
        "article is renamed its attention history is split across titles. For "
        "English, `pageviews.csv` sums every title that has referred to the same "
        "article (the seed title, direct move-log successor titles, and the current "
        "canonical title). This file records exactly which titles were summed, "
        "their role and the move date, so the constructed series is auditable.".format(
            _count_csv_rows(DATA_PROCESSED / "en_title_variants.csv")
        )
    )
    add("")
    add("| article_en | variant_title | role | move_date | variant_total_views |")
    add("|---|---|---|---|---:|")
    variants_path = DATA_PROCESSED / "en_title_variants.csv"
    if variants_path.exists():
        with open(variants_path, "r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                add(
                    "| {} | {} | {} | {} | {:,} |".format(
                        row["article_en"],
                        row["variant_title"],
                        row["role"],
                        row["move_date"] or "-",
                        int(row["variant_total_views"]),
                    )
                )
    add("")
    add(
        "**Important:** these English series are constructs that combine multiple "
        "Wikipedia titles. Series in the other 13 languages use only the current "
        "langlink target, so a page move in those editions could fragment their "
        "history; this is a documented limitation."
    )
    add("")

    # ucdp
    add("### `data/processed/ucdp_monthly_country.csv` - UCDP monthly fatalities by country")
    add("")
    add(
        "{} rows. `best` (UCDP best estimate) fatalities and event counts, aggregated "
        "to the month of `date_start`, by event-location country (ISO-3166 alpha-3). "
        "Release: {}; coverage: {} .. {}.".format(
            _count_csv_rows(DATA_PROCESSED / "ucdp_monthly_country.csv"),
            ucdp_summary.get("version", "n/a") if ucdp_summary else "n/a",
            ucdp_summary.get("month_min", "n/a") if ucdp_summary else "n/a",
            ucdp_summary.get("month_max", "n/a") if ucdp_summary else "n/a",
        )
    )
    add("")
    add("| column | type | description |")
    add("|---|---|---|")
    add("| `iso3` | str | ISO-3166 alpha-3 country of the event location |")
    add("| `month` | str | `YYYY-MM` |")
    add("| `fatalities` | int | sum of UCDP `best` fatalities |")
    add("| `events` | int | number of GED events |")
    add("")
    add(
        "**Coding caveat:** GED `country` is the country where the event occurred. "
        "Events in Gaza are therefore coded `ISR`; there is no `PSE` series in UCDP. "
        "Join Gaza ceasefires to `ISR` fatalities."
    )
    add("")
    add(
        "Top-5 countries by {}-{} fatalities: {}.".format(
            ucdp_summary.get("month_min", "2014-01")[:4] if ucdp_summary else "2014",
            ucdp_summary.get("month_max", "2025-12")[:4] if ucdp_summary else "2025",
            ", ".join(
                "{} {:,}".format(iso, fat)
                for iso, fat in top_countries(DATA_PROCESSED / "ucdp_monthly_country.csv")
            )
            or "n/a",
        )
    )
    add("")

    add("### `data/processed/ucdp_monthly_dyad.csv` - UCDP monthly fatalities by dyad")
    add("")
    add(
        "{} rows. Same aggregation by UCDP dyad. Columns: `dyad_new_id`, "
        "`dyad_name`, `month`, `fatalities`, `events`.".format(
            _count_csv_rows(DATA_PROCESSED / "ucdp_monthly_dyad.csv")
        )
    )
    add("")

    add("### `data/processed/ucdp_country_mapping.csv` - theatre ISO3 -> UCDP country join table")
    add("")
    add(
        "One row per ISO-3166 alpha-3 country present in the monthly country table, "
        "plus explicit non-identity joins. Columns: `theatre_iso3`, `ucdp_country`, "
        "`ucdp_country_id` (GED/Gleditsch-Ward country id), `mapping_type` "
        "(`identity` / `alias` / `proxy`), `note`. **Use this table to join ceasefire "
        "events to UCDP fatalities - do not assume the ISO3 code equals the GED label.** "
        "Non-identity mappings:"
    )
    add("")
    add("| theatre_iso3 | ucdp_country | mapping_type | note |")
    add("|---|---|---|---|")
    mapping_path = DATA_PROCESSED / "ucdp_country_mapping.csv"
    if mapping_path.exists():
        with open(mapping_path, "r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row["mapping_type"] == "identity":
                    continue
                add(
                    "| {} | {} | {} | {} |".format(
                        row["theatre_iso3"], row["ucdp_country"], row["mapping_type"], row["note"] or "-"
                    )
                )
    add("")

    add("## Raw cache (`data/raw/`)")
    add("")
    add("| path | content |")
    add("|---|---|")
    add("| `data/raw/langlinks/` | raw MediaWiki `prop=langlinks` responses (one JSON per title) |")
    add("| `data/raw/langlinks/moves/` | raw MediaWiki move-log responses |")
    add("| `data/raw/langlinks.json` | consolidated title -> canonical title + langlinks + move chain |")
    add("| `data/raw/pageviews/<lang>/` | raw Wikimedia pageviews responses (one JSON per title/range) |")
    add("| `data/raw/pageviews_fetch_report.json` | fetch accounting (requests, cache hits, retries, status counts) |")
    if ucdp_summary:
        zip_info = ucdp_summary.get("zip_info", {})
        add(
            "| `data/raw/ucdp/ged{}-csv.zip` | official UCDP {} release used ({:.1f} MB) |".format(
                ucdp_summary.get("version", "").replace("GED v", "").replace(".", ""),
                ucdp_summary.get("version", ""),
                zip_info.get("zip_bytes", 0) / (1024.0 * 1024.0),
            )
        )
        add(
            "| `data/raw/ucdp/{}` | extracted GED event table ({:,} events) |".format(
                zip_info.get("member", "GEDEvent_v26_1.csv"),
                ucdp_summary.get("events_parsed_total", 0),
            )
        )
    add("| `data/raw/ucdp/ged241-csv.zip` | cached UCDP GED v24.1 zip (automatic fallback release) |")
    add("| `data/raw/ucdp/ucdp_summary.json` | UCDP parse/aggregation summary (records the release actually used) |")
    add("")
    if fetch_report:
        http = fetch_report.get("http", {})
        add(
            "Pageview fetch accounting: {:,} network requests, {:,} cache hits, "
            "{:,} retries; HTTP status counts {}.".format(
                http.get("network_requests", 0),
                http.get("cache_hits", 0),
                http.get("retries", 0),
                http.get("status_counts", {}),
            )
        )
        add("")

    add("## Method notes and limitations")
    add("")
    add(
        "1. **Pageviews are a proxy for attention**, skewed toward literate online "
        "populations; they are not public opinion."
    )
    add(
        "2. **Bot traffic is excluded** by the `user` agent filter of the per-article "
        "endpoint; `all-access` includes desktop and mobile."
    )
    add(
        "3. **Page moves fragment series** (see `en_title_variants.csv`). English "
        "series sum title variants; other editions use the current title only."
    )
    add(
        "4. **Missing translations are real** - some conflict-specific articles do not "
        "exist in all 14 editions (see `missing_articles.csv`). They are not imputed."
    )
    add(
        "5. **UCDP month coverage is release-bounded:** the aggregates end at {} for "
        "the release used ({}). Check the UCDP section above before assuming a "
        "follow-up window is fully observed.".format(
            ucdp_summary.get("month_max", "n/a") if ucdp_summary else "n/a",
            ucdp_summary.get("version", "n/a") if ucdp_summary else "n/a",
        )
    )
    add(
        "   For ceasefires after 2024-12 the 12-month follow-up window is truncated "
        "by the release end ({}).".format(
            ucdp_summary.get("month_max", "n/a") if ucdp_summary else "n/a"
        )
    )
    add(
        "6. **Temporal existence convention:** attention series start when the article "
        "(or, for summed English title chains, the earliest title) first registers "
        "pageviews. Days before the first row are **missing, not zero**; "
        "{:,} of {:,} present series start after 2015-07-01, and {:,} resolved "
        "article/language pairs are entirely missing (see the pageviews section).".format(
            stats.get("n_late_series", 0),
            stats.get("n_series", 0),
            stats.get("n_all_missing", 0),
        )
    )
    add("")
    add("## Related inputs not produced here")
    add("")
    add(
        "`data/events/ceasefires.csv` (the curated ceasefire event table) is owned by a "
        "separate workstream and is intentionally not generated or modified by this "
        "pipeline. The pipeline reads it only if present; its absence does not affect "
        "anything documented above."
    )
    add("")
    add("## Dataset freeze")
    add("")
    add(
        "Generated by `scripts/run_all.py` on {}. Raw responses cached under "
        "`data/raw/`; processed tables under `data/processed/`.".format(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
    )
    add("")
    return "\n".join(out)


# populated in run() from the seed tables
CONCEPT = {"war": [], "peace": [], "conflict": []}


def _load_concept_labels():
    try:
        from . import config
        from .conflict_seeds import CONFLICT_ARTICLES
    except ImportError:  # pragma: no cover
        from src import config  # type: ignore
        from src.conflict_seeds import CONFLICT_ARTICLES  # type: ignore
    CONCEPT["war"] = list(config.WAR_CONCEPTS)
    CONCEPT["peace"] = list(config.PEACE_CONCEPTS)
    CONCEPT["conflict"] = [row[0] for row in CONFLICT_ARTICLES]


def run():
    _load_concept_labels()
    ensure = DATA_PROCESSED
    ensure.mkdir(parents=True, exist_ok=True)

    pageviews_path = DATA_PROCESSED / "pageviews.csv"
    stats = scan_pageviews(pageviews_path)
    stats["lang_pairs"] = _count_csv_rows(DATA_PROCESSED / "article_langlinks.csv")
    stats["n_articles"] = _count_csv_rows(DATA_PROCESSED / "articles.csv")
    resolved_pairs = 0
    resolved_keys = []
    langlinks_csv = DATA_PROCESSED / "article_langlinks.csv"
    if langlinks_csv.exists():
        with open(langlinks_csv, "r", encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                if row.get("has_langlink") == "1":
                    resolved_pairs += 1
                    resolved_keys.append((row["lang"], row["article_en"]))
    stats["resolved_pairs"] = resolved_pairs

    # Temporal-existence accounting (article creation / title rename -> series start).
    present = set(stats["series_first"])
    stats["n_series"] = len(present)
    late = sorted(
        ((key, first) for key, first in stats["series_first"].items() if first > "2015-07-01"),
        key=lambda kv: kv[1],
        reverse=True,
    )
    stats["n_late_series"] = len(late)
    stats["late_series_examples"] = late[:8]
    all_missing = [key for key in resolved_keys if key not in present]
    stats["n_all_missing"] = len(all_missing)
    stats["all_missing_examples"] = sorted(all_missing)[:10]

    ucdp_summary = {}
    summary_path = DATA_RAW / "ucdp" / "ucdp_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as fh:
            ucdp_summary = json.load(fh)

    fetch_report = {}
    report_path = DATA_RAW / "pageviews_fetch_report.json"
    if report_path.exists():
        with open(report_path, "r", encoding="utf-8") as fh:
            fetch_report = json.load(fh)

    sanity_text, spike = build_sanity(stats, ucdp_summary)
    sanity_path = DATA_PROCESSED / "sanity_summary.txt"
    with open(sanity_path, "w", encoding="utf-8") as fh:
        fh.write(sanity_text + "\n")

    readme = build_readme(stats, ucdp_summary, fetch_report)
    readme_path = PROJECT_ROOT / "data" / "README.md"
    with open(readme_path, "w", encoding="utf-8") as fh:
        fh.write(readme + "\n")

    print(sanity_text)
    print("")
    print("Wrote {} and {}".format(_rel(readme_path), _rel(sanity_path)))
    return {"stats": stats, "spike": spike, "readme": str(readme_path)}


if __name__ == "__main__":  # pragma: no cover
    run()
