# Data dictionary - The Half-Life of Peace

Daily multilingual Wikipedia attention series (2015-07-01 to 2025-11-01) and monthly UCDP conflict-fatality aggregates (2014 to 2025), built by the reproducible pipeline in `src/` and orchestrated by `scripts/run_all.py`.

- **Data retrieval date:** 2026-11-07
- **Project root:** `/Users/ahmedjaffar/Documents/deepseek-harness/default-workspace/peace-halflife`
- **Total pageview rows:** 1,736,563 across 14 languages and 50 articles
- **Pageview date coverage:** 2015-07-01 .. 2025-11-01
- **UCDP release used:** GED v26.1 (https://ucdp.uu.se/downloads/ged/ged261-csv.zip); monthly coverage 2014-01 .. 2025-12

## Repro

```bash
# from the repository root, with the project venv
.venv/bin/python scripts/run_all.py                 # data pipeline (uses cache)
.venv/bin/python scripts/run_all.py --refresh       # force re-download
.venv/bin/python scripts/run_all.py --stage analysis # delegate to analysis/run.py --stage analysis
.venv/bin/python scripts/run_all.py --stage figures  # figures from cached analysis artifacts
.venv/bin/python scripts/run_all.py --stage all      # data + analysis + figures
```

Every raw HTTP response is cached verbatim under `data/raw/`; a re-run replays the cache and makes **no** network requests unless `--refresh` is passed. The pipeline is therefore idempotent, resumable and runnable offline after the first successful download. Requests use a global ~5 req/s limiter, at most 5 worker threads, exponential backoff on 429/5xx, and an identifying User-Agent.

## Provenance

| Source | Endpoint / file | Version | Retrieved |
|---|---|---|---|
| Wikimedia pageviews (per-article, daily) | `https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{lang}.wikipedia/all-access/user/{article}/daily/{start}00/{end}00` | REST API v1 | 2026-11-07 |
| Wikipedia interlanguage links | `https://en.wikipedia.org/w/api.php?action=query&prop=langlinks&lllimit=500&format=json&redirects=1&titles=<title>` | MediaWiki API | 2026-11-07 |
| Wikipedia page-move logs | `https://en.wikipedia.org/w/api.php?action=query&list=logevents&letype=move&letitle=<title>` | MediaWiki API | 2026-11-07 |
| UCDP Georeferenced Event Dataset (GED) | `https://ucdp.uu.se/downloads/ged/ged261-csv.zip` | GED v26.1 | 2026-11-07 |

## Study design constants

- Languages (14): en, ar, es, fr, de, ru, zh, fa, tr, id, pt, uk, he, hi
- WAR concept basket (10): War, Armed conflict, Civil war, Invasion, Airstrike, Genocide, Terrorism, Military occupation, Refugee, War crime
- PEACE concept basket (11): Peace, Ceasefire, Peace treaty, Peacebuilding, Mediation, Diplomacy, Reconciliation (theology), Disarmament, Demobilization, Peacekeeping, Humanitarian aid
- Conflict-specific articles: 30
- Article/language cells: 700 (50 articles x 14 languages); resolved to an article: 644; missing translations: 56

## Files

### `data/processed/seeds.csv` - seed table

51 rows. One row per seed article: the 10 WAR concepts, 11 PEACE concepts and 30 conflict-specific articles defined in `src/config.py` and `src/conflict_seeds.py`.

| column | type | description |
|---|---|---|
| `seed_title` | str | English Wikipedia title as specified in the seed list |
| `concept` | str | concept label for WAR/PEACE rows (empty for conflict rows) |
| `family` | str | `war` / `peace` / `conflict` |
| `conflict` | str | conflict label (conflict rows only) |
| `country_iso3` | str | primary theatre country (conflict rows only) |
| `region` | str | coarse region (conflict rows only) |

### `data/processed/articles.csv` - canonical article table

50 rows. One row per **unique canonical English article**, after resolving redirects and merging seeds that collapse onto the same article (e.g. `Armed conflict` -> `War`). Columns: `article_en`, `seed_titles` (`|`-joined), `concepts`, `family`, `conflict`, `country_iso3`, `region`, `n_langs_resolved`, `missing_langs`.

### `data/processed/article_langlinks.csv` - multilingual title map

700 rows. One row per (article, language) for all 14 languages. `has_langlink=0` means the article does not exist in that language edition (it is logged in `missing_articles.csv` and skipped). Columns: `article_en`, `family`, `lang`, `article_local`, `has_langlink`.

### `data/processed/pageviews.csv` - daily attention series (main dataset)

**1,736,563 rows**, 14 languages, 50 articles, 2015-07-01 to 2025-11-01.

| column | type | description |
|---|---|---|
| `lang` | str | Wikipedia language edition code (`en`, `ar`, ...) |
| `article_en` | str | canonical English article title (the join key) |
| `article_local` | str | title used in that language edition (canonical English title for `en`) |
| `date` | str | `YYYY-MM-DD` (daily) |
| `views` | int | pageviews, all-access / user agents only (bot traffic excluded) |

Language coverage:

| lang | rows | articles | date coverage |
|---|---:|---:|---|
| `en` | 161,067 | 50 | 2015-07-01 .. 2025-11-01 |
| `ar` | 124,327 | 46 | 2015-07-01 .. 2025-11-01 |
| `es` | 129,958 | 49 | 2015-07-01 .. 2025-11-01 |
| `fr` | 141,917 | 45 | 2015-07-01 .. 2025-11-01 |
| `de` | 125,539 | 42 | 2015-07-01 .. 2025-11-01 |
| `ru` | 136,416 | 47 | 2015-07-01 .. 2025-11-01 |
| `zh` | 131,095 | 47 | 2015-07-01 .. 2025-11-01 |
| `fa` | 98,611 | 45 | 2015-07-01 .. 2025-11-01 |
| `tr` | 118,582 | 43 | 2015-07-01 .. 2025-11-01 |
| `id` | 133,826 | 49 | 2015-07-01 .. 2025-11-01 |
| `pt` | 129,027 | 48 | 2015-07-01 .. 2025-11-01 |
| `uk` | 120,770 | 46 | 2015-07-01 .. 2025-11-01 |
| `he` | 113,279 | 47 | 2015-07-01 .. 2025-11-01 |
| `hi` | 72,149 | 26 | 2015-07-01 .. 2025-11-01 |

#### Temporal existence convention (important for baselines/WPAR)

A row in `pageviews.csv` exists only from the day a series first registers pageviews - i.e. from article creation (or from the earliest title in the summed title chain for English). **Days before a series' first row are MISSING, not zero.** Filling them with 0 would understate pre-creation baselines and distort the War-Peace Attention Ratio; availability-aware aggregation must treat them as absent.

- 630 article/language series are present; **303 start after 2015-07-01** because the article (or title) did not exist earlier.
- Latest series onsets: Sudanese civil war (2023–present) (ru, first row 2025-10-29); Gaza war (ar, first row 2025-10-09); Russo-Ukrainian war (2022–present) (fa, first row 2025-10-08); Insurgency in the Maghreb (2002–present) (fr, first row 2025-09-21); Gaza war (he, first row 2025-08-16); Insurgency in Khyber Pakhtunkhwa (uk, first row 2025-08-08); Hezbollah–Israel conflict (2023–present) (he, first row 2025-07-13); Gaza war (pt, first row 2025-06-18).
- **14 langlink-resolved article/language pairs have no pageview rows at all** (article exists in the edition but the pageviews API returned nothing); they are kept as all-missing and logged in `missing_articles.csv`.
- All-missing examples: Insurgency in Khyber Pakhtunkhwa (ar); Myanmar civil war (2021–present) (ar); Sudanese civil war (2023–present) (ar); South Sudanese Civil War (fa); Hezbollah–Israel conflict (2023–present) (fr); Myanmar civil war (2021–present) (fr); Sudanese civil war (2023–present) (fr); Boko Haram insurgency (hi); Mexican drug war (hi); Peace treaty (hi).

### `data/processed/missing_articles.csv` - missing translations / pages

70 rows. Diagnostics for article/language pairs that could not be fetched. `reason` is one of `no_langlink` (no article in that language), `http_404` (page does not exist for the pageviews API) or `no_items` (empty series). These rows are *absent* from `pageviews.csv`; they are genuine data limitations, not fetch failures.

### `data/processed/en_title_variants.csv` - English page-move summation

14 rows. MediaWiki records pageviews **per title string**, so when an article is renamed its attention history is split across titles. For English, `pageviews.csv` sums every title that has referred to the same article (the seed title, direct move-log successor titles, and the current canonical title). This file records exactly which titles were summed, their role and the move date, so the constructed series is auditable.

| article_en | variant_title | role | move_date | variant_total_views |
|---|---|---|---|---:|
| Hezbollah–Israel conflict (2023–present) | Israel–Hezbollah conflict (2023–2024) | seed | 2025-04-21 | 78,096 |
| Hezbollah–Israel conflict (2023–present) | Israel–Hezbollah conflict (2023–present) | move_target | 2025-04-21 | 2,167,672 |
| Hezbollah–Israel conflict (2023–present) | Hezbollah–Israel conflict (2023–present) | canonical | - | 413 |
| Russo-Ukrainian war (2022–present) | Russian invasion of Ukraine | seed | 2025-09-23 | 21,741,556 |
| Russo-Ukrainian war (2022–present) | 2022 Russian invasion of Ukraine | move_target | 2025-09-25 | 57,101,264 |
| Russo-Ukrainian war (2022–present) | Russo-Ukrainian war (2022–present) | canonical | 2025-09-23 | 391,107 |
| Sudanese civil war (2023–present) | War in Sudan (2023) | seed | 2023-09-03 | 906,472 |
| Sudanese civil war (2023–present) | War in Sudan (2023–present) | move_target | 2024-01-04 | 693,860 |
| Sudanese civil war (2023–present) | 2023 Sudan conflict | move_target | 2023-09-03 | 1,771,857 |
| Sudanese civil war (2023–present) | Sudanese civil war (2023–present) | canonical | - | 3,517,307 |
| Tigray war | Tigray War | seed | 2024-09-13 | 4,009,219 |
| Tigray war | Tigray war | canonical | 2024-09-13 | 284,584 |
| War | War | canonical | - | 6,540,474 |
| War | Armed conflict | seed | - | 168,806 |

**Important:** these English series are constructs that combine multiple Wikipedia titles. Series in the other 13 languages use only the current langlink target, so a page move in those editions could fragment their history; this is a documented limitation.

### `data/processed/ucdp_monthly_country.csv` - UCDP monthly fatalities by country

5782 rows. `best` (UCDP best estimate) fatalities and event counts, aggregated to the month of `date_start`, by event-location country (ISO-3166 alpha-3). Release: GED v26.1; coverage: 2014-01 .. 2025-12.

| column | type | description |
|---|---|---|
| `iso3` | str | ISO-3166 alpha-3 country of the event location |
| `month` | str | `YYYY-MM` |
| `fatalities` | int | sum of UCDP `best` fatalities |
| `events` | int | number of GED events |

**Coding caveat:** GED `country` is the country where the event occurred. Events in Gaza are therefore coded `ISR`; there is no `PSE` series in UCDP. Join Gaza ceasefires to `ISR` fatalities.

Top-5 countries by 2014-2025 fatalities: UKR 368,139, ETH 333,572, SYR 282,314, AFG 186,647, MEX 114,597.

### `data/processed/ucdp_monthly_dyad.csv` - UCDP monthly fatalities by dyad

20443 rows. Same aggregation by UCDP dyad. Columns: `dyad_new_id`, `dyad_name`, `month`, `fatalities`, `events`.

### `data/processed/ucdp_country_mapping.csv` - theatre ISO3 -> UCDP country join table

One row per ISO-3166 alpha-3 country present in the monthly country table, plus explicit non-identity joins. Columns: `theatre_iso3`, `ucdp_country`, `ucdp_country_id` (GED/Gleditsch-Ward country id), `mapping_type` (`identity` / `alias` / `proxy`), `note`. **Use this table to join ceasefire events to UCDP fatalities - do not assume the ISO3 code equals the GED label.** Non-identity mappings:

| theatre_iso3 | ucdp_country | mapping_type | note |
|---|---|---|---|
| ARE | United Arab Emirates | alias | - |
| CIV | Ivory Coast | alias | - |
| COD | DR Congo (Zaire) | alias | - |
| COG | Congo | alias | - |
| GBR | United Kingdom | alias | - |
| KHM | Cambodia (Kampuchea) | alias | - |
| MDG | Madagascar (Malagasy) | alias | - |
| MMR | Myanmar (Burma) | alias | - |
| PSE | Israel | proxy | GED codes the event-location country; events in Gaza and the West Bank appear under Israel. GED has no PSE rows, so join Gaza/PSE ceasefires to Israeli fatalities. |
| RUS | Russia (Soviet Union) | alias | - |
| SWZ | Kingdom of eSwatini (Swaziland) | alias | - |
| USA | United States of America | alias | - |
| YEM | Yemen (North Yemen) | alias | - |

## Raw cache (`data/raw/`)

| path | content |
|---|---|
| `data/raw/langlinks/` | raw MediaWiki `prop=langlinks` responses (one JSON per title) |
| `data/raw/langlinks/moves/` | raw MediaWiki move-log responses |
| `data/raw/langlinks.json` | consolidated title -> canonical title + langlinks + move chain |
| `data/raw/pageviews/<lang>/` | raw Wikimedia pageviews responses (one JSON per title/range) |
| `data/raw/pageviews_fetch_report.json` | fetch accounting (requests, cache hits, retries, status counts) |
| `data/raw/ucdp/ged261-csv.zip` | official UCDP GED v26.1 release used (37.3 MB) |
| `data/raw/ucdp/GEDEvent_v26_1.csv` | extracted GED event table (417,968 events) |
| `data/raw/ucdp/ged241-csv.zip` | cached UCDP GED v24.1 zip (automatic fallback release) |
| `data/raw/ucdp/ucdp_summary.json` | UCDP parse/aggregation summary (records the release actually used) |

Pageview fetch accounting: 0 network requests, 653 cache hits, 0 retries; HTTP status counts {}.

## Method notes and limitations

1. **Pageviews are a proxy for attention**, skewed toward literate online populations; they are not public opinion.
2. **Bot traffic is excluded** by the `user` agent filter of the per-article endpoint; `all-access` includes desktop and mobile.
3. **Page moves fragment series** (see `en_title_variants.csv`). English series sum title variants; other editions use the current title only.
4. **Missing translations are real** - some conflict-specific articles do not exist in all 14 editions (see `missing_articles.csv`). They are not imputed.
5. **UCDP month coverage is release-bounded:** the aggregates end at 2025-12 for the release used (GED v26.1). Check the UCDP section above before assuming a follow-up window is fully observed.
   For ceasefires after 2024-12 the 12-month follow-up window is truncated by the release end (2025-12).
6. **Temporal existence convention:** attention series start when the article (or, for summed English title chains, the earliest title) first registers pageviews. Days before the first row are **missing, not zero**; 303 of 630 present series start after 2015-07-01, and 14 resolved article/language pairs are entirely missing (see the pageviews section).

## Related inputs not produced here

`data/events/ceasefires.csv` (the curated ceasefire event table) is owned by a separate workstream and is intentionally not generated or modified by this pipeline. The pipeline reads it only if present; its absence does not affect anything documented above.

## Dataset freeze

Generated by `scripts/run_all.py` on 2026-11-07 22:09:05. Raw responses cached under `data/raw/`; processed tables under `data/processed/`.

