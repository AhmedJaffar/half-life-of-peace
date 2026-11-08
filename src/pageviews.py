"""Fetch daily Wikipedia pageviews per article per language, 2015-07-01..2025-11-01.

Endpoint (verified by the project lead and re-verified here)::

    https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/
        {lang}.wikipedia/all-access/user/{article}/daily/{start}00/{end}00

The full ten-year range is accepted in a single call; if an edition rejects it
with HTTP 400 the range is retried in <=2-year chunks (also cached).

Engineering properties
----------------------
* Every raw JSON response is cached under ``data/raw/pageviews/<lang>/``.
  A re-run rebuilds ``data/processed/pageviews.csv`` from cache with **zero**
  network calls (unless ``refresh=True``).
* At most ``MAX_WORKERS`` threads, global ~5 req/s limiter, exponential backoff
  on 429/5xx, identifying User-Agent (see common.py).
* Titles are URL-encoded with ``quote(title, safe="")``.
* Missing articles (no translation in a language edition, HTTP 404, or an empty
  response) are logged to ``data/processed/missing_articles.csv``; the run never
  crashes because a translation does not exist.

Title-variant continuity (page moves)
-------------------------------------
MediaWiki records pageviews *per title string*, so when an article is renamed its
attention history is split across the old and new titles.  For English we
therefore **sum** every title that has referred to the same article: the seed
title(s), the current canonical title, and any intermediate titles discovered in
the MediaWiki move log (``data/processed/en_title_variants.csv`` records exactly
which titles were summed, their role and the move date).  For the other 13
language editions only the current langlink target is fetched - a documented
limitation in data/README.md.

Public helper ``fetch_many(tasks)`` implements the interface used by
``scripts/fetch_concepts.py``: ``tasks`` is an iterable of
``(lang, article, start_yyyymmdd, end_yyyymmdd)`` and the return value maps each
task to ``{yyyymmdd: views}`` (or ``{"_error": ...}`` if the request failed).
It re-uses the full-range cache, so it runs offline after ``run()`` has fetched
the same articles.
"""
from __future__ import annotations

import csv
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import quote

try:  # normal package import (run_all / from src import pageviews)
    from .common import DATA_PROCESSED, DATA_RAW
    from .common import MAX_WORKERS, HttpCache, ensure_dirs, log, sha1_key
except ImportError:  # pragma: no cover - direct `python src/pageviews.py`
    sys.path[:] = [p for p in sys.path if p != str(Path(__file__).resolve().parent)]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.common import DATA_PROCESSED, DATA_RAW  # type: ignore  # noqa: F401
    from src.common import MAX_WORKERS, HttpCache, ensure_dirs, log, sha1_key  # type: ignore

START_TS = "2015070100"
END_TS = "2025110100"

LANG_LIST = ["en", "ar", "es", "fr", "de", "ru", "zh", "fa", "tr", "id", "pt", "uk", "he", "hi"]

BASE_URL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{lang}.wikipedia/all-access/user/{article}/daily/{start}/{end}"
)

COLUMNS = ["lang", "article_en", "article_local", "date", "views"]


# ---------------------------------------------------------------------------
# URL / cache helpers
# ---------------------------------------------------------------------------
def build_url(lang: str, article_local: str, start: str = START_TS, end: str = END_TS) -> str:
    return BASE_URL.format(
        lang=lang, article=quote(article_local, safe=""), start=start, end=end
    )


def cache_path_for(lang: str, article_local: str, start: str, end: str) -> Path:
    key = sha1_key("|".join([lang, article_local, start, end]))
    return DATA_RAW / "pageviews" / lang / (key + ".json")


def _norm_ts(ts: str) -> str:
    """Accept ``YYYYMMDD`` or ``YYYYMMDD00`` and return the 10-char API form."""
    ts = str(ts).strip()
    if len(ts) == 8:
        return ts + "00"
    return ts


def _ymd(ts: str) -> str:
    return ts[:8]


def _date_chunks(start_ts: str, end_ts: str, max_days: int = 730):
    """Split a YYYYMMDD00 range into <= max_days windows (400 fallback)."""
    start = datetime.strptime(_ymd(start_ts), "%Y%m%d")
    end = datetime.strptime(_ymd(end_ts), "%Y%m%d")
    chunks = []
    cursor = start
    while cursor <= end:
        chunk_end = min(cursor + timedelta(days=max_days - 1), end)
        chunks.append(
            (cursor.strftime("%Y%m%d") + "00", chunk_end.strftime("%Y%m%d") + "00")
        )
        cursor = chunk_end + timedelta(days=1)
    return chunks


def _env_items(envelope) -> dict:
    """Return {yyyymmdd: views} for a 200 envelope (empty dict otherwise)."""
    if not envelope or envelope.get("status") != 200:
        return {}
    out = {}
    for item in (envelope.get("body") or {}).get("items") or []:
        out[_ymd(item["timestamp"])] = out.get(_ymd(item["timestamp"]), 0) + int(
            item.get("views", 0)
        )
    return out


# ---------------------------------------------------------------------------
# fetching
# ---------------------------------------------------------------------------
def _fetch_range_envs(cache, lang, article_en, article_local, start, end, mode):
    """Fetch (or replay) one range, with <=2-year chunk fallback on HTTP 400."""
    meta = {
        "lang": lang,
        "article_en": article_en,
        "article_local": article_local,
        "start": start,
        "end": end,
        "mode": mode,
    }
    env, _ = cache.get_json(
        build_url(lang, article_local, start, end),
        cache_path_for(lang, article_local, start, end),
        meta=meta,
    )
    if env.get("status") == 400:
        chunk_mode = "chunk" if mode == "full" else "range_chunk"
        envelopes = []
        for s, e in _date_chunks(start, end):
            env2, _ = cache.get_json(
                build_url(lang, article_local, s, e),
                cache_path_for(lang, article_local, s, e),
                meta={
                    "lang": lang,
                    "article_en": article_en,
                    "article_local": article_local,
                    "start": s,
                    "end": e,
                    "mode": chunk_mode,
                },
            )
            envelopes.append(env2)
            if env2.get("status") != 200:
                break
        return envelopes
    return [env]


def _classify(envs):
    """Return (kind, items_dict) with kind in ok/missing/error."""
    statuses = [e.get("status") for e in envs]
    if not envs:
        return "error", {}
    if any(s == 404 for s in statuses):
        return "missing", {}
    if not all(s == 200 for s in statuses):
        return "error", {}
    merged = {}
    for env in envs:
        for ymd, views in _env_items(env).items():
            merged[ymd] = merged.get(ymd, 0) + views
    if not merged:
        return "missing", {}
    return "ok", merged


def fetch_one(cache, lang, article_en, article_local):
    """Fetch one full-window series; returns (kind, payload).

    ``kind`` is ``ok`` / ``missing`` / ``error``.  The raw response(s) are cached
    as a side effect, which is what the rebuilt CSV reads.
    """
    envs = _fetch_range_envs(
        cache, lang, article_en, article_local, START_TS, END_TS, mode="full"
    )
    kind, items = _classify(envs)
    if kind == "ok":
        return "ok", {"series": len(items), "from_cache": all(e.get("_cached") for e in envs)}
    if kind == "missing":
        status = envs[0].get("status") if envs else None
        reason = "http_404" if status == 404 else "no_items"
        return "missing", {
            "lang": lang,
            "article_en": article_en,
            "article_local": article_local,
            "reason": reason,
            "http_status": status,
        }
    return "error", {
        "lang": lang,
        "article_en": article_en,
        "article_local": article_local,
        "reason": "http_{}".format(envs[0].get("status") if envs else "?"),
        "http_status": envs[0].get("status") if envs else None,
        "text": (envs[0].get("text") if envs else "")[:200],
    }


def fetch_many(tasks, cache=None):
    """Interface used by ``scripts/fetch_concepts.py``.

    ``tasks``: iterable of ``(lang, article, start, end)`` where start/end are
    ``YYYYMMDD`` or ``YYYYMMDD00``.  Returns ``{task: {yyyymmdd: views}}``;
    failures map to ``{"_error": "..."}`` and genuinely missing pages to ``{}``.

    Subsets of the full fetched window are served from the full-range cache, so
    this runs offline once ``run()`` has populated the cache.
    """
    cache = cache or HttpCache(DATA_RAW)
    task_list = list(tasks)

    def _one(task):
        try:
            lang, article, start, end = task
            start, end = _norm_ts(start), _norm_ts(end)
            # 1) serve from the full-range cache when the request is a subset
            if (
                _ymd(start) >= _ymd(START_TS)
                and _ymd(end) <= _ymd(END_TS)
                and article
            ):
                full_env = cache.load_cached(cache_path_for(lang, article, START_TS, END_TS))
                if full_env is not None and full_env.get("status") == 200:
                    series = {
                        ymd: views
                        for ymd, views in _env_items(full_env).items()
                        if _ymd(start) <= ymd <= _ymd(end)
                    }
                    return task, series
            # 2) otherwise fetch the exact range (cached separately, ignored by
            #    the main pageviews.csv rebuild, which uses mode=full/chunk only)
            envs = _fetch_range_envs(
                cache, lang, article, article, start, end, mode="range"
            )
            kind, series = _classify(envs)
            if kind == "ok":
                return task, series
            if kind == "missing":
                return task, {}
            return task, {"_error": "HTTP {}".format(envs[0].get("status") if envs else "?")}
        except Exception as exc:  # noqa: BLE001 - caller expects error dicts
            return task, {"_error": repr(exc)[:200]}

    results = {}
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = [pool.submit(_one, task) for task in task_list]
        for future in as_completed(futures):
            task, value = future.result()
            results[task] = value
    return results


# ---------------------------------------------------------------------------
# rebuild the tidy table from cached raw responses
# ---------------------------------------------------------------------------
def _load_cached_envelopes():
    root = DATA_RAW / "pageviews"
    envelopes = []
    if not root.exists():
        return envelopes
    for path in sorted(root.rglob("*.json")):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                envelope = json.load(fh)
        except (ValueError, OSError):
            continue
        meta = envelope.get("meta") or {}
        if meta.get("mode") not in ("full", "chunk"):
            continue  # range caches from fetch_many are not part of pageviews.csv
        if not meta.get("lang") or not meta.get("article_en"):
            continue
        envelopes.append(envelope)
    return envelopes


def rebuild_from_cache():
    """Build pageviews.csv + missing list from the raw cache.

    Returns ``(rows, missing, variant_totals)`` where variant_totals maps
    ``(lang, article_en, variant_title) -> total views``.
    """
    envelopes = _load_cached_envelopes()

    groups = {}
    for env in envelopes:
        meta = env["meta"]
        key = (meta["lang"], meta["article_en"])
        group = groups.setdefault(key, {"full": {}, "chunks": [], "meta": meta})
        if meta.get("mode") == "full":
            group["full"][meta["article_local"]] = env
        else:
            group["chunks"].append(env)

    rows = []
    missing = []
    variant_totals = {}
    for (lang, article_en), group in sorted(groups.items()):
        meta = group["meta"]
        variant_series = {}

        for variant_title, env in group["full"].items():
            if env.get("status") == 200:
                series = _env_items(env)
                if series:
                    variant_series[variant_title] = series
            elif env.get("status") == 404:
                missing.append(
                    {
                        "lang": lang,
                        "article_en": article_en,
                        "article_local": variant_title,
                        "reason": "http_404",
                        "http_status": 404,
                    }
                )

        for env in group["chunks"]:
            if env.get("status") == 200:
                variant_title = env["meta"]["article_local"]
                bucket = variant_series.setdefault(variant_title, {})
                for ymd, views in _env_items(env).items():
                    bucket[ymd] = bucket.get(ymd, 0) + views
            elif env.get("status") == 404:
                missing.append(
                    {
                        "lang": lang,
                        "article_en": article_en,
                        "article_local": env["meta"]["article_local"],
                        "reason": "http_404_chunked",
                        "http_status": 404,
                    }
                )

        if not variant_series:
            already_404 = any(
                m.get("lang") == lang
                and m.get("article_en") == article_en
                and str(m.get("reason", "")).startswith("http_404")
                for m in missing
            )
            if not already_404:
                missing.append(
                    {
                        "lang": lang,
                        "article_en": article_en,
                        "article_local": meta.get("article_local", ""),
                        "reason": "no_series",
                        "http_status": None,
                    }
                )
            continue

        # ---- sum title variants (page-move reconstruction) -----------------
        combined = {}
        for variant_title, series in variant_series.items():
            total = 0
            for ymd, views in series.items():
                combined[ymd] = combined.get(ymd, 0) + views
                total += views
            variant_totals[(lang, article_en, variant_title)] = total

        article_local = article_en if lang == "en" else sorted(variant_series)[0]
        for ymd in sorted(combined):
            rows.append(
                (
                    lang,
                    article_en,
                    article_local,
                    "{}-{}-{}".format(ymd[0:4], ymd[4:6], ymd[6:8]),
                    combined[ymd],
                )
            )

    ensure_dirs(DATA_PROCESSED)
    out_path = DATA_PROCESSED / "pageviews.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        writer.writerows(rows)

    missing_path = DATA_PROCESSED / "missing_articles.csv"
    with open(missing_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["lang", "article_en", "article_local", "reason", "http_status"])
        seen = set()
        for item in sorted(missing, key=lambda x: (x["lang"], x["article_en"], x["reason"])):
            sig = (item["lang"], item["article_en"], item["article_local"], item["reason"])
            if sig in seen:
                continue
            seen.add(sig)
            writer.writerow(
                [
                    item["lang"],
                    item["article_en"],
                    item["article_local"],
                    item["reason"],
                    item["http_status"] if item["http_status"] is not None else "",
                ]
            )
    return rows, missing, variant_totals


# ---------------------------------------------------------------------------
# English title variants (page-move reconstruction bookkeeping)
# ---------------------------------------------------------------------------
def _en_variants(article_en, seed_titles, langlinks_mapping):
    """Return ordered list of (variant_title, role, move_date) for an article."""
    variants = []
    seen = set()

    def _add(title, role, move_date=""):
        if title and title not in seen:
            seen.add(title)
            variants.append((title, role, move_date))

    for seed in seed_titles:
        info = langlinks_mapping.get(seed, {})
        chain = info.get("move_chain") or []
        seed_move_dates = [
            mv.get("move_date", "")
            for mv in chain
            if mv.get("from") == seed and mv.get("move_date")
        ]
        seed_move_date = min(seed_move_dates) if seed_move_dates else ""
        _add(seed, "seed", seed_move_date)
        for mv in chain:
            _add(mv.get("target"), "move_target", mv.get("move_date", ""))
    _add(article_en, "canonical", "")
    return variants


def write_en_title_variants(variant_totals, articles, langlinks_mapping):
    """Record which English titles were summed per article (audit table)."""
    path = DATA_PROCESSED / "en_title_variants.csv"
    n_rows = 0
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "article_en",
                "variant_title",
                "role",
                "move_date",
                "variant_total_views",
                "note",
            ]
        )
        for article_en in sorted(articles):
            seed_titles = [t for t in articles[article_en]["seed_titles"].split("|") if t]
            variants = _en_variants(article_en, seed_titles, langlinks_mapping)
            if len(variants) <= 1:
                continue
            for title, role, move_date in variants:
                if title == article_en:
                    role = "canonical"
                writer.writerow(
                    [
                        article_en,
                        title,
                        role,
                        move_date,
                        variant_totals.get(("en", article_en, title), 0),
                        "summed into the English article series",
                    ]
                )
                n_rows += 1
    log("pageviews: {} English title-variant rows -> {}".format(n_rows, path))
    return n_rows


# ---------------------------------------------------------------------------
# main entry point
# ---------------------------------------------------------------------------
def run(refresh: bool = False):
    ensure_dirs(DATA_RAW / "pageviews", DATA_PROCESSED)
    cache = HttpCache(DATA_RAW, refresh=refresh)

    articles_path = DATA_PROCESSED / "articles.csv"
    langlinks_path = DATA_PROCESSED / "article_langlinks.csv"
    if not articles_path.exists() or not langlinks_path.exists():
        raise RuntimeError("Run src/langlinks.py first (articles.csv is missing)")

    articles = {}
    with open(articles_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            articles[row["article_en"]] = row

    with open(DATA_RAW / "langlinks.json", "r", encoding="utf-8") as fh:
        langlinks_mapping = json.load(fh)

    local_titles = {}
    with open(langlinks_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["has_langlink"] == "1":
                local_titles[(row["article_en"], row["lang"])] = row["article_local"]

    # ---- build fetch task list --------------------------------------------
    tasks = []
    no_langlink = []
    for article_en, row in articles.items():
        seed_titles = [t for t in row["seed_titles"].split("|") if t]
        for variant, _role, _mdate in _en_variants(article_en, seed_titles, langlinks_mapping):
            tasks.append(("en", article_en, variant))
        for lang in LANG_LIST:
            if lang == "en":
                continue
            local = local_titles.get((article_en, lang))
            if local:
                tasks.append((lang, article_en, local))
            else:
                no_langlink.append(
                    {
                        "lang": lang,
                        "article_en": article_en,
                        "article_local": "",
                        "reason": "no_langlink",
                        "http_status": None,
                    }
                )

    log(
        "pageviews: {} series to fetch ({} resolved article/language pairs; {} missing "
        "langlinks) with {} workers".format(
            len(tasks), len(local_titles), len(no_langlink), MAX_WORKERS
        )
    )

    results = {"ok": 0, "missing": 0, "error": 0}
    errors = []
    lock = threading.Lock()
    counter = {"done": 0}

    def _worker(task):
        lang, article_en, article_local = task
        kind, payload = fetch_one(cache, lang, article_en, article_local)
        with lock:
            counter["done"] += 1
            done = counter["done"]
            if done % 100 == 0 or done == len(tasks):
                log("pageviews: {}/{} series processed".format(done, len(tasks)))
        return kind, payload

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(_worker, task): task for task in tasks}
        for future in as_completed(futures):
            kind, payload = future.result()
            results[kind] = results.get(kind, 0) + 1
            if kind == "error":
                errors.append(payload)

    # ---- rebuild tidy outputs from the raw cache --------------------------
    rows, missing, variant_totals = rebuild_from_cache()
    write_en_title_variants(variant_totals, articles, langlinks_mapping)

    # merge the langlink-time misses into the missing-article log
    all_missing = no_langlink + missing
    missing_path = DATA_PROCESSED / "missing_articles.csv"
    with open(missing_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["lang", "article_en", "article_local", "reason", "http_status"])
        seen = set()
        for item in sorted(all_missing, key=lambda x: (x["lang"], x["article_en"], x["reason"])):
            sig = (item["lang"], item["article_en"], item["article_local"], item["reason"])
            if sig in seen:
                continue
            seen.add(sig)
            writer.writerow(
                [
                    item["lang"],
                    item["article_en"],
                    item["article_local"],
                    item["reason"],
                    item["http_status"] if item["http_status"] is not None else "",
                ]
            )

    dates = [r[3] for r in rows]
    report = {
        "retrieval_date": "2026-11-07",
        "start": "2015-07-01",
        "end": "2025-11-01",
        "tasks": len(tasks),
        "fetch_results": results,
        "errors": errors[:50],
        "http": cache.stats.as_dict(),
        "rows": len(rows),
        "series": len({(r[0], r[1]) for r in rows}),
        "languages": sorted({r[0] for r in rows}),
        "articles": len({r[1] for r in rows}),
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "missing_rows": len(seen),
    }
    with open(DATA_RAW / "pageviews_fetch_report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)

    log(
        "pageviews: {} rows, {} article/language series, dates {}..{}; "
        "{} network requests, {} cache hits, {} retries; {} missing entries -> {}".format(
            len(rows),
            report["series"],
            report["date_min"],
            report["date_max"],
            cache.stats.network_requests,
            cache.stats.cache_hits,
            cache.stats.retries,
            len(seen),
            DATA_PROCESSED / "pageviews.csv",
        )
    )
    if errors:
        log("pageviews: {} errors (first: {})".format(len(errors), errors[0]))
    return report


if __name__ == "__main__":  # pragma: no cover
    run(refresh="--refresh" in sys.argv)
