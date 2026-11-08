"""Resolve seed English article titles across 14 Wikipedia language editions.

Seeds
-----
* WAR and PEACE concept baskets come from :mod:`src.config`
  (``WAR_CONCEPTS``, ``PEACE_CONCEPTS``; the project's single source of truth).
  ``Reconciliation`` is mapped to the encyclopaedic article
  ``Reconciliation (theology)`` - the bare title is a 4-langlink disambiguation
  page, which is not a usable attention target.
* Conflict-specific seeds come from :mod:`src.conflict_seeds`.

Resolution
----------
Uses the MediaWiki action API ``action=query&prop=langlinks`` on en.wikipedia
with ``redirects=1`` so moved/renamed seed titles resolve to their current
canonical title.  Every response is cached under ``data/raw/langlinks/`` and the
consolidated mapping is written to ``data/raw/langlinks.json``.

Outputs
-------
data/raw/langlinks.json               requested title -> canonical page + langlinks
data/processed/seeds.csv              the seed table (concept + conflict seeds)
data/processed/articles.csv           unique canonical articles + metadata
data/processed/article_langlinks.csv   one row per article x language (14 langs)

Important detail recorded for downstream use: several English seeds are
redirects to a different canonical title (e.g. ``Armed conflict`` -> ``War``,
``Russian invasion of Ukraine`` -> ``Russo-Ukrainian war (2022–present)``).
Because MediaWiki records pageviews *per title string*, a page move splits the
attention series.  ``pageviews.py`` therefore sums the pageview series of the
seed title(s) and the canonical title for English; seeds that collapse onto the
same canonical article are merged here so no article is counted twice.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
from urllib.parse import urlencode

try:  # normal package import (run via scripts/run_all.py or `from src import ...`)
    from .common import (
        DATA_PROCESSED,
        DATA_RAW,
        HttpCache,
        ensure_dirs,
        log,
        sha1_key,
    )
    from . import config
    from .conflict_seeds import conflict_seed_rows
except ImportError:  # pragma: no cover - direct `python src/langlinks.py`
    import sys

    _here = str(Path(__file__).resolve().parent)
    sys.path[:] = [p for p in sys.path if p != _here]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.common import (  # type: ignore  # noqa: F401
        DATA_PROCESSED,
        DATA_RAW,
        HttpCache,
        ensure_dirs,
        log,
        sha1_key,
    )
    from src import config  # type: ignore  # noqa: F401
    from src.conflict_seeds import conflict_seed_rows  # type: ignore  # noqa: F401

LANGUAGES = list(config.LANGS)

API_URL = "https://en.wikipedia.org/w/api.php"
LL_LIMIT = 500

# Concepts whose bare English title is not a usable article.
TITLE_OVERRIDES = {"Reconciliation": "Reconciliation (theology)"}

SEED_COLUMNS = ["seed_title", "concept", "family", "conflict", "country_iso3", "region"]


def build_seed_rows():
    """Combine the config concept baskets and the conflict seeds."""
    rows = []
    for family, concepts in (("war", config.WAR_CONCEPTS), ("peace", config.PEACE_CONCEPTS)):
        for concept in concepts:
            rows.append(
                {
                    "seed_title": TITLE_OVERRIDES.get(concept, concept),
                    "concept": concept,
                    "family": family,
                    "conflict": "",
                    "country_iso3": "",
                    "region": "",
                }
            )
    rows.extend(conflict_seed_rows())
    return rows


def write_seeds(seed_rows):
    ensure_dirs(DATA_PROCESSED)
    path = DATA_PROCESSED / "seeds.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SEED_COLUMNS)
        writer.writeheader()
        writer.writerows(seed_rows)
    log("seeds: {} seed articles -> {}".format(len(seed_rows), path))
    return path


def _langlinks_url(title: str) -> str:
    params = {
        "action": "query",
        "titles": title,
        "prop": "langlinks",
        "lllimit": str(LL_LIMIT),
        "format": "json",
        "redirects": "1",
    }
    return API_URL + "?" + urlencode(params)


def _cache_path(title: str) -> Path:
    return DATA_RAW / "langlinks" / (sha1_key(title) + ".json")


def _moves_url(title: str) -> str:
    params = {
        "action": "query",
        "list": "logevents",
        "letype": "move",
        "letitle": title,
        "lelimit": "50",
        "format": "json",
    }
    return API_URL + "?" + urlencode(params)


def _moves_cache_path(title: str) -> Path:
    return DATA_RAW / "langlinks" / "moves" / (sha1_key(title) + ".json")


def _resolve_moves(cache, title: str):
    """Return [{target, move_date}] for page moves whose source title was ``title``."""
    envelope, _ = cache.get_json(
        _moves_url(title), _moves_cache_path(title), meta={"move_log_for": title}
    )
    if envelope.get("status") != 200:
        return []
    events = ((envelope.get("body") or {}).get("query") or {}).get("logevents") or []
    moves = []
    for event in events:
        if event.get("type") != "move":
            continue
        if event.get("title") != title:
            continue
        params = event.get("params") or {}
        target = params.get("target_title")
        if not target or target == title or params.get("target_ns") not in (0, "0"):
            continue
        moves.append(
            {
                "from": title,
                "target": target,
                "move_date": str(event.get("timestamp", ""))[:10],
            }
        )
    return moves


def _move_chain(cache, start_title: str, max_depth: int = 1):
    """Return the direct successor titles in the page-move log of ``start_title``.

    MediaWiki stores pageviews per title string, so every successor title may
    hold part of the article's attention history (e.g. ``Russian invasion of
    Ukraine`` -> ``Russo-Ukrainian war (2022–present)`` and
    ``2022 Russian invasion of Ukraine``).  Only the *direct* move targets are
    kept: deeper traversal follows title reuse (vandal moves such as
    ``Ukraine 1``, ``Russia 0``) rather than the same article, so it is not
    sound.  These titles are summed for English and the chain is written to
    data/processed/en_title_variants.csv.
    """
    chain = []
    seen = {start_title}
    queue = [(start_title, 0)]
    while queue:
        title, depth = queue.pop(0)
        if depth >= max_depth:
            continue
        for move in _resolve_moves(cache, title):
            target = move["target"]
            chain.append(move)
            if target not in seen:
                seen.add(target)
                queue.append((target, depth + 1))
    return chain


def _parse_response(envelope, requested_title: str):
    """Extract (canonical_title, {lang: local_title}, missing) from a response."""
    body = envelope.get("body") or {}
    pages = (body.get("query") or {}).get("pages") or {}
    if not pages:
        return requested_title, {}, True
    page = next(iter(pages.values()))
    if "missing" in page or "invalid" in page:
        return requested_title, {}, True
    page_title = page.get("title") or requested_title
    langlinks = {}
    for item in page.get("langlinks", []) or []:
        lang = item.get("lang")
        local = item.get("*") or item.get("title")
        if lang and local:
            langlinks[lang] = local
    if body.get("continue"):
        log("WARNING: langlinks truncated for {}".format(requested_title))
    return page_title, langlinks, False


def run(refresh: bool = False):
    """Resolve all seeds.  Returns (articles, langlinks_mapping)."""
    ensure_dirs(DATA_RAW / "langlinks", DATA_PROCESSED)
    cache = HttpCache(DATA_RAW, refresh=refresh)
    seed_rows = build_seed_rows()
    write_seeds(seed_rows)

    mapping = {}
    for seed in seed_rows:
        title = seed["seed_title"]
        envelope, from_cache = cache.get_json(
            _langlinks_url(title), _cache_path(title), meta={"seed_title": title}
        )
        if envelope.get("status") != 200:
            log(
                "langlinks: FAILED {} (HTTP {}) - treating as missing".format(
                    title, envelope.get("status")
                )
            )
            canonical, langlinks, missing = title, {}, True
        else:
            canonical, langlinks, missing = _parse_response(envelope, title)
        # Follow the MediaWiki move log only for titles that actually redirected:
        # these are the cases where pageview history is split across titles.
        move_chain = []
        if not missing and canonical != title:
            move_chain = _move_chain(cache, title)
            if move_chain:
                log(
                    "langlinks: {} moved; title variants: {}".format(
                        title, ", ".join(m["target"] for m in move_chain)
                    )
                )
        mapping[title] = {
            "seed_title": title,
            "page_title": canonical,
            "missing": missing,
            "langlinks": langlinks,
            "fetched_at": envelope.get("fetched_at"),
            "from_cache": from_cache,
            "move_chain": move_chain,
        }

    with open(DATA_RAW / "langlinks.json", "w", encoding="utf-8") as fh:
        json.dump(mapping, fh, ensure_ascii=False, indent=2, sort_keys=True)

    # ---- merge seeds that redirect to the same canonical article ----------
    articles = {}
    for seed in seed_rows:
        seed_title = seed["seed_title"]
        info = mapping[seed_title]
        canonical = info["page_title"]
        article = articles.get(canonical)
        if article is None:
            article = {
                "article_en": canonical,
                "seed_titles": [],
                "concepts": [],
                "family": seed["family"],
                "conflict": seed["conflict"],
                "country_iso3": seed["country_iso3"],
                "region": seed["region"],
                "langlinks": {},
                "missing": info["missing"],
            }
            articles[canonical] = article
        else:
            log(
                "langlinks: merging seed {!r} into canonical {!r}".format(seed_title, canonical)
            )
        article["seed_titles"].append(seed_title)
        if seed["concept"]:
            article["concepts"].append(seed["concept"])
        for lang, local in info["langlinks"].items():
            article["langlinks"].setdefault(lang, local)

    # ---- write consolidated outputs ---------------------------------------
    articles_path = DATA_PROCESSED / "articles.csv"
    with open(articles_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(
            [
                "article_en",
                "seed_titles",
                "concepts",
                "family",
                "conflict",
                "country_iso3",
                "region",
                "n_langs_resolved",
                "missing_langs",
            ]
        )
        for canonical in sorted(articles):
            a = articles[canonical]
            resolved = sum(1 for lang in LANGUAGES if lang == "en" or lang in a["langlinks"])
            missing_langs = ",".join(
                lang for lang in LANGUAGES if lang != "en" and lang not in a["langlinks"]
            )
            writer.writerow(
                [
                    canonical,
                    "|".join(a["seed_titles"]),
                    "|".join(a["concepts"]),
                    a["family"],
                    a["conflict"],
                    a["country_iso3"],
                    a["region"],
                    resolved,
                    missing_langs,
                ]
            )

    langlinks_path = DATA_PROCESSED / "article_langlinks.csv"
    missing_langlinks = 0
    with open(langlinks_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["article_en", "family", "lang", "article_local", "has_langlink"])
        for canonical in sorted(articles):
            a = articles[canonical]
            writer.writerow([canonical, a["family"], "en", canonical, 1])
            for lang in LANGUAGES:
                if lang == "en":
                    continue
                local = a["langlinks"].get(lang)
                if local:
                    writer.writerow([canonical, a["family"], lang, local, 1])
                else:
                    missing_langlinks += 1
                    writer.writerow([canonical, a["family"], lang, "", 0])

    n_lang_pairs = sum(
        1
        for a in articles.values()
        for lang in LANGUAGES
        if lang == "en" or lang in a["langlinks"]
    )
    log(
        "langlinks: {} unique articles from {} seed titles; {} article/language pairs "
        "resolved, {} missing langlinks -> {}".format(
            len(articles), len(seed_rows), n_lang_pairs, missing_langlinks, langlinks_path
        )
    )
    return articles, mapping


if __name__ == "__main__":  # pragma: no cover
    run(refresh="--refresh" in __import__("sys").argv)
