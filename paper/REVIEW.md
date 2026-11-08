# Adversarial review — *The Half-Life of Peace*

**Reviewer:** independent adversarial reviewer (teammate `reviewer`)
**Review date:** 2026-11-07 (America/Toronto), cutoff ~22:15 local
**Inputs inspected:** `paper/manuscript.md` (862 lines), `paper/references.bib`, `paper/related_work.md`,
`paper/gap_risks.md`, `README.md`, `DESIGN.md`, `LICENSE`, `CITATION.cff`, `Makefile`, `scripts/*.py`,
`src/*.py`, `analysis/{pipeline,models,report,figures,run,selftest,config_analysis}.py`,
`analysis/results.json`, `analysis/report.md`, `analysis/tables/*`, `analysis/manifest.json`,
`figures/*`, `data/README.md`, `data/events/*`, `docs/events_method.md`, and the processed CSVs.
**Independent work performed:** offline re-run of the data pipeline; independent re-computation of the
PAHL, WPAR, event-study, mapping and resumption results from the frozen inputs; Crossref/Semantic Scholar
verification of all 65 bibliography DOIs; live retrieval of 12 cited ceasefire source pages; inspection
of the placebo/null design and the outcome-coding code; a genuine attempt at `make all`/`make check`/PDF build.

**Status of the manuscript.** `paper/manuscript.md` still contains **18 unresolved `[TK]` placeholders**
(the entire Findings paragraph of the abstract, Table 1 volume cells, and the sample-description block) and
**has no Results, Discussion, Limitations, Conclusion or reference list** (it stops at §4.10). The analysis
outputs (`analysis/results.json`, `analysis/report.md`, `analysis/tables/`, 10 figures) appeared at 22:08 and
are complete. The manuscript is therefore **incomplete as a submission**, independent of everything below.

Severity counts: **6 BLOCKER, 13 MAJOR, 12 MINOR, and 9 verified-OK areas.**
Verdict at the end.

---

## A. BLOCKERS — the paper cannot be submitted with any of these unresolved

### A1. The pre-registered placebo test fails: PAHL is not shown to be event-specific — BLOCKER
`analysis/results.json` → `placebo`; `analysis/report.md:9,159-166`; design in
`src/metrics.py:911-1075` and `analysis/pipeline.py:761-877`; falsification condition in
`paper/manuscript.md:600-612` and `DESIGN.md:76-79`.

The observed median PAHL is **41.80 days**; the median under 500 random same-year placebo dates per event
is **55.29 days** (8,236 successful placebo fits; null 95% interval 38.5–75.5). Empirical one-sided
p = **0.926**, two-sided p = **0.156**; **0 of 24 events** has an upper-tail placebo p ≤ 0.05.
The pre-registered falsification condition — "if the observed PAHL distribution is indistinguishable from
the placebo distribution, then attention decay around ceasefires is not event-specific" — is therefore *met*.
The analysis report says so in plain terms: *"The measure as implemented therefore does not isolate a
ceasefire-specific decay."* The manuscript cannot describe PAHL as a measured, ceasefire-specific decay
and cannot headline it as a successful measurement. The same report's §8 conclusion is correct and should
be the paper's: *"the two inferential claims — event-specific decay and PAHL-based prediction — are not
established by these data."*
**Fix:** rewrite the Abstract/Findings, §5 and §6 around the null (the placebo is a substantive result, not a
footnote); state the one-sided and two-sided p and the 0/24 event result; delete any sentence that treats
the 41.8-day value as an estimate of a ceasefire-specific half-life; promote `analysis/report.md` §7.1 and
§8 into the manuscript. Note also that even a *directional* test in the "real announcements decay faster"
direction gives p ≈ 0.074 (1 − 0.926), i.e. still not significant at 5%.

### A2. The headline number depends on the estimator by an order of magnitude — BLOCKER
`analysis/results.json` → `robustness.window_sensitivity`; `analysis/report.md:167-172`;
`src/metrics.py:856-977`; `analysis/pipeline.py:325-350`.

The same definition ("days for excess attention to fall to half its peak") yields, on the same events:

| estimator / window | median PAHL (days) | n |
|---|---:|---:|
| non-parametric half-peak crossing (180-d horizon) | **5.5** | 24 |
| Theil–Sen fit, 30-day window | **15.7** | 23 |
| Theil–Sen fit, 90-day window (**headline**) | **41.8** | 24 |
| Theil–Sen fit, 270-day window | **173.5** | 20 |
| pooled event-study curve (independent) | half-peak by **day 14** | 34 |

Four of the 24 fitted events are pinned exactly at the 90-day censoring value (23.3% of language fits are
censored), so the median is partly a property of the chosen window, not of attention. The paper must not
present 41.8 as "the" half-life without showing this table and reconciling it with Figure 1, which visually
returns to baseline in roughly two weeks. **Fix:** make the estimator-dependence a primary result, report the
crossing estimator and the event-study half-peak alongside the model estimate, and either use a survival
model for the censored half-lives or explicitly rename the quantity (e.g. "90-day censored decay parameter")
so it is not confused with a half-life. If the paper keeps one headline number, it must be the interval that
spans this estimator uncertainty, not a point estimate.

### A3. The resumption outcome is invalid for several key events — BLOCKER
`src/metrics.py:1473-1588` (`post_positions = range(event_pos, event_pos + horizon)`, line 1581;
threshold `0.25 × pre_mean`); `analysis/results.json` → `resumption`;
`data/events/ceasefires_metadata.json` → `balance_note`.

The 12-month "post" window starts with the **event month**, so it contains pre-ceasefire violence whenever
the announcement is not on the 1st, and the threshold is a fraction of a 6-month mean that can be near zero.
Concrete demonstrable false positives against the curator's own `balance_note` judgements and against the
public record:

- `gaza_2021` (21 May 2021): pre-6-month ISR mean = 0.17 fatalities → threshold = 0.04. ISR May 2021 = 254
  (the 11-day war, all of it *before* the 21 May ceasefire), June = 3, July = 1. Coded **resumed at t = 0**
  even though this ceasefire is widely assessed to have held. Any single fatality would flip it.
- `gaza_2022` (7 Aug 2022): pre-mean 5.0, threshold 1.25; Aug = 30 (the 5–7 Aug escalation), Sept = 11…
  coded **resumed at t = 0** although the truce held into 2023.
- `colombia_farc_2016`: pre-mean 6.7, threshold 1.7; Sept = 9, Oct = 3, Nov = 4, Dec = 9, Jan = 14… — coded
  **resumed at t = 0** even though FARC demobilised; country-level totals conflate residual ELN/other violence.
- `india_pak_2021`: PAK country series (threshold 9) is dominated by internal insurgency (Feb = 55), not the
  LoC; coded **resumed at t = 0** although the LoC ceasefire broadly held.
- 22 of 25 "resumptions" occur at t = 0 (the event month), i.e. the variable mostly records *continuation*
  of pre-existing violence, not resumption. The resulting base rate is 75.8% (25/33), against the curator's
  ex-ante expectation of roughly 11 held / 15 eroded / 10 collapsed.

Because the only positive result (AUC 0.775, OR 5.32) rests on **5 negative events**, one or two corrected
labels can move it materially (the report itself says a single event "moves the estimates substantially").
**Fix (concrete):** (i) start the post window in the month *after* the event month, or use event-day daily
data; (ii) require an absolute floor (e.g. ≥ N fatalities) in addition to the ratio so near-zero baselines do
not make any fatality "resumption"; (iii) validate the coded events against the event table's `balance_note`
and report the disagreement; (iv) map the theatre conflict specifically (dyad series), not the whole country;
(v) re-run the prediction with the corrected outcome and publish the sensitivity. Until then the predictive
claim is not supported.

### A4. The Methods section does not describe the estimator that was actually run — BLOCKER
Manuscript vs code/report:

| Method as written in `paper/manuscript.md` | What the code does | Reference |
|---|---|---|
| baseline is a "28-day centred moving average" with ±14-day mask (line 620) | PAHL uses a **fixed median log attention over [−90,−30] days**; the rolling baseline is used only for the event-study curve and one sensitivity | `src/metrics.py:559-619,743-770`; `analysis/config_analysis.py` |
| peak searched in a "seven-day-to-thirty-day window after the announcement" (line 655) | peak searched in **[t0, t0+14]** (`PEAK_END=14`) | `src/config.py:60`; `src/metrics.py:71` |
| "Huber M-estimation is the primary fit" (line 678) | **Theil–Sen is the primary estimator**; Huber is only a sensitivity | `src/metrics.py:911-977`; `analysis/pipeline.py:544`; `analysis/report.md:61` |
| model includes and estimates a residual offset `c` (lines 673-677) | no offset is estimated; days below 5% of peak are dropped | `src/metrics.py:953-968` |
| "residual bootstrap for per-event slopes" (line 698) | not implemented anywhere (only a bootstrap over events for the median) | `src/metrics.py:1049-1079` |
| "reports results … on the pre-registered alternative [date] convention" (line 532) | no alternative-date analysis exists; the event table has no alternative-date field | `analysis/pipeline.py` (no reference) |

A reader cannot reproduce the headline from §4 as written. **Fix:** rewrite §4.1 and §4.3 to describe the
implemented estimator exactly (fixed pre-event median baseline; peak [0,+14]; 7-day centred median
smoothing; floor at 5% of peak; Theil–Sen; censoring at 90 days; one-language minimum), delete the offset,
Huber-as-primary and residual-bootstrap claims (or implement them), and delete the alternative-date claim
or implement it.

### A5. The UCDP GED version is misstated throughout — BLOCKER
`paper/manuscript.md:545,597` ("version 24.1", "UCDP GED v24.1"); `README.md:42`;
`DESIGN.md:39`; `data/events/ceasefires_metadata.json` (`ucdp_join_note`);
`scripts/verify_claims.py:28` (whitelists `24.1` so the guard cannot catch it).

The data actually used and frozen is **GED v26.1** (`data/README.md:9,28,121`;
`data/raw/ucdp/ged261-csv.zip`; `src/ucdp.py:53` `GED_VERSION = "26.1"`;
`analysis/report.md:265,763`). The v24.1 file is only a cached fallback. This is a factual
data-provenance error: the paper cites a different dataset release from the one that produced every number.
**Fix:** change every occurrence to GED v26.1 (and update the UCDP citation year/version accordingly), or
re-run on v24.1 and accept the loss of 2025 follow-up. Do not leave the discrepancy.

### A6. The manuscript is incomplete — BLOCKER
`paper/manuscript.md` has 18 `[TK]` placeholders (abstract Findings and Volume paragraph, Table 1 volume cells,
§3.5 sample description) and no §5–§8, no Results, no Discussion, no Limitations, no Conclusion, no
references. `make check` returns `BLOCKER: 18 unresolved [TK] placeholders` and exit code 2.
**Fix:** write Phase 2 from `analysis/report.md`/`results.json` only, then re-run `make check`. Until then this
is a draft, not a preprint.

---

## B. MAJOR findings

### B1. The one "significant" result does not survive multiplicity correction, and the survival model is null — MAJOR
`analysis/results.json` → `robustness.fdr`, `prediction`, `survival`; `analysis/report.md:194-198,205`.
Raw permutation p = 0.033 and CV AUC = 0.775 look promising, but:
- Benjamini–Hochberg across the 8 reported tests leaves **0 significant** (adjusted p = 0.145 for the
  permutation test and the Spearman p = 0.0405; adjusted 0.145); the report states this.
- The Cox model is null: HR 1.27 (0.83–1.93), p = 0.273, n = 23.
- Spearman permutation p = 0.052.
- OR 95% CI 0.74–38.2 (Wald, n = 23 with 5 negatives) includes 1 and is essentially uninformative.
**Fix:** in the manuscript, report the FDR result and the survival null next to the raw p; do not describe the
association as significant, and keep the word "exploratory" on every sentence that quotes OR/AUC.

### B2. The association disappears at the 50% resumption threshold — MAJOR
`analysis/results.json` → `robustness.threshold_sensitivity`; `analysis/report.md:183-187`.
At 10% and 25% the outcome coding is identical in the prediction sample (OR 5.32, CV AUC 0.775); at 50% the
OR falls to 1.66 (0.57–4.88), p = 0.355, CV AUC 0.587. The threshold is an arbitrary design choice and it
drives the result. The report says the result "should not be described as threshold-robust"; the manuscript
must say the same in the Results and Abstract, not only in a robustness note.

### B3. The multilingual claim is much weaker than the prose implies — MAJOR
`analysis/results.json` → `meta`, `pahl.per_event`, `pahl.by_language`; `analysis/report.md:28-58`;
`data/processed/pageviews.csv`; `data/README.md` (limits note 3).
- Only **24 of 36** events yield a PAHL; 12 are excluded (`too_few_language_fits`), including Minsk II,
  Mali 2015, the Myanmar NCA, Doha 2020, the Jeddah 2023 ceasefire and the Israel–Hezbollah 2024 ceasefire.
- Of the 24 fitted events, **6 use a single language edition** and 9 use ≤ 2 editions; only 18 are
  "multilingual" (≥2 editions). Most of the single-language fits are English.
- Per-language medians are computed from different event subsets (n_fitted 1 for fa, 4 for ar/uk, 8 for
  en/ru/he/fr, 12 for tr); they are not a valid cross-language comparison as presented (a language with one
  event is compared to a language with twelve). A proper test needs a within-event paired comparison.
- Title moves fragment non-English series: e.g. the **Arabic "Gaza war" series begins 2025-10-09** and the
  **Hebrew series begins 2025-08-16**, so the Arabic/Hebrew audiences are absent for every Gaza event
  (2021, 2022, 2023, 2025); `uk` "Gaza war" has 33 rows/13 views in 2025. This is exactly the audience the
  paper says it wants to compare.
**Fix:** report 24/36 and the per-event language count in the abstract/Table 1; drop or re-frame the
per-language medians; add the paired within-event language contrast; state the Arabic/Hebrew Gaza gap in
Limitations and in the Data section; rename "fourteen language editions" to "up to fourteen editions,
median n per event = X".

### B4. Several event→article mappings measure the wrong conflict — MAJOR
`analysis/tables/table1_events.csv` (mapping columns); `analysis/pipeline.py:179-310`.
- `philippines_2016` (Duterte/CPP-NPA ceasefire) → **"Philippine drug war"** (wrong conflict).
- `myanmar_nca_2015` (2015 NCA) → **"Myanmar civil war (2021–present)"** (article created in 2021; no
  2015 data, which is why it fails).
- `india_pak_2025` (India–Pakistan ceasefire) → **"Insurgency in Khyber Pakhtunkhwa"** (wrong conflict).
- `israel_iran_2025`, `thai_camb_2025` are unmapped.
These are not cosmetic: the first three contribute to the PAHL sample (india_pak_2025 has a 31.3-day
estimate from the wrong article), and the mapping heuristic is doing more work than the "auditable" prose
suggests. **Fix:** hand-review the 34 mappings; map by conflict, not country; re-run; report the corrected
mapping table and a sensitivity excluding `country_unique`/`country_multi_best` mappings.

### B5. The novelty claims are contradicted by existing work — MAJOR
`paper/manuscript.md:131-132,144-147,395-397`; `paper/related_work.md:102,150,152`.
The paper says pageviews have "not been used for attention to armed conflict" and that "we found no study
that uses pageviews to measure attention to armed conflict" (after claiming searches of OpenAlex/Crossref/
Semantic Scholar). Counterexamples found in one Crossref/Semantic Scholar pass:
- **Oswald, C. & Ohrenhofer, D. (2022). "Click, click boom: Using Wikipedia data to predict changes in
  battle-related deaths." *International Interactions* 48(4), doi:10.1080/03050629.2022.2061969.**
  They explicitly treat country Wikipedia **pageviews as a measure of interest/salience** and use it to
  predict battle-related deaths. This is directly prior use of pageviews as a conflict-attention measure
  and a conflict predictor, and it should have appeared in the claimed search.
- **Reynal-Querol, Baeza-Yates, Motte & Scabbia, "How long do we pay attention to a war?", RES/BSC
  success story (May 2026)** — 10m news articles, 2000–2024, reports that coverage drops away within about
  3 months and studies attention decay to armed conflicts. This contradicts "prior work on attention to
  conflict ... measures attention as a level rather than a rate" (`related_work.md:150`).
Neither is in `references.bib`. **Fix:** add both, cite them in the gap section, and narrow the claim to
what survives (no prior work estimates a half-life *for ceasefire announcements*, and none joins decay to
resumption). The honest wording is "we are not aware of a study that ..."; do not claim the search found none.

### B6. "Pre-registered" claims are not supported by any registration — MAJOR
`paper/manuscript.md:439` ("the pre-registered directional expectation of the project is the negative one"),
`:532` ("pre-registered alternative convention"), and `:792` ("Six families of checks are pre-specified").
`DESIGN.md:76-79` lists falsification conditions but is a design memo committed in the scaffold, not a
registration; it does not state the negative direction, and it does not contain the alternative date
convention. There is no OSF/registry link anywhere in the repo or manuscript.
**Fix:** replace "pre-registered" with "specified in advance in the project design document (`DESIGN.md`)"
(or deposit a dated registration and cite it), and drop the "alternative convention" claim or implement it.

### B7. The third pre-registered falsification condition is triggered but not enforced — MAJOR
`analysis/pipeline.py:1119-1165` (`_falsification_section`); `analysis/results.json` → `falsification`;
`analysis/report.md:205`; `DESIGN.md:76-79`.
The war/peace comparison gives **war PAHL 65.3 vs peace PAHL 81.6 days** (peace decays *slower*), so the
pre-registered condition "attention to PEACE concepts decays more slowly than WAR concepts → the
attention-deficit framing that motivates WPAR is wrong" is met. The result carries the direction string
`peace_decays_slower`, but `verdicts` contains only `["placebo_fail"]`; the third falsification condition is
never turned into a verdict and the report does not flag it as a failed condition. (The paired median
difference is 0.0 with a wide CI, so the evidence is weak, but the pre-registered rule was stated
categorically.) **Fix:** have `_falsification_section` emit a verdict for the war/peace direction; report it
in the Results and Discussion exactly as pre-specified, including the paired-difference CI.

### B8. `verify_claims.py` cannot do the job it is advertised to do — MAJOR
`scripts/verify_claims.py:50-57,28`; `paper/manuscript.md:614-625` claims a verification script checks "each
numeric claim ... matches the machine-readable results file".
The `matches()` function rounds both sides to 0/1/2/3 decimals and accepts a match at any rounding: the true
value 41.802568 accepts claims of **41.8, 41.81, 42.0 and 42.4** (demonstrated by importing the module), and
the whitelist silently passes all numbers 0–30, years, and `24.1` (which is how the wrong GED version evaded
the check). It cannot catch a misquoted median, an off-by-one n, or a wrong GED version.
**Fix:** match on exact values with a stated tolerance, remove `24.1` from the whitelist, and require every
number quoted in the Results to be present with its label (e.g. `pahl.median`) rather than as a loose token.
Also add a numeric unit test that deliberately corrupts a number and asserts the checker fails.

### B9. `make all` / `make analysis` / `make figures` are broken, and the README tells users to run them — MAJOR
`Makefile:6,18-23`; `scripts/run_all.py:68-100`; `README.md:56-60`.
`make analysis` runs `scripts/run_all.py --stage analysis`, but `run_all.py` has no `--stage` argument
(only `--refresh`, `--only`, `--ged-version`): `argparse` errors with "unrecognized arguments: --stage
analysis". `make figures` fails identically. The analysis actually lives in `analysis/run.py`. So the
one-command reproduction path advertised in the README does not work as written; only the data stage does.
**Fix:** point the Makefile at `$(PY) analysis/run.py --stage analysis|figures` (and `check` after Phase 2),
and test `make all` from a clean copy before claiming one-command reproduction.

### B10. The bibliography has four syntax errors — MAJOR
`paper/references.bib:678-679, 686-687, 694-695, 702-703`.
`@book{jones2005}`, `@book{baumgartner1993}`, `@book{fortna2008}` and `@book{moeller1999}` are missing the
comma after `year = {...}` before `url = {...}`. BibTeX/pandoc-citeproc will either error or silently drop
the url; the reference list cannot be built cleanly.
**Fix:** add the commas. (Also see C1 for the Greek Mu typo and C2 for the translated title.)

### B11. The claim that every event has a pre-announcement baseline is false — MAJOR
`paper/manuscript.md:469-471` ("so that every event in the sample has a pre-announcement baseline of several
months"). The pageview panel starts 2015-07-01; `minsk2_2015` (2015-02-15) and `mali_2015` (2015-06-20)
have **no pageview data before the event**, and 12 events have no usable PAHL for this or related reasons
(articles created/renamed after the event). **Fix:** state the actual coverage rule (events before ~2015-08
and events whose article post-dates the event cannot enter PAHL), and report 24/36 explicitly.

### B12. The licence statement is not backed by a data/manuscript licence — MAJOR
`LICENSE` (MIT only); `README.md:74-76` ("Data and manuscript: CC BY 4.0");
`paper/manuscript.md:428-430` ("The curated ceasefire table is released with this paper under CC BY 4.0").
No CC BY 4.0 text or notice exists in the repo, and MIT does not cover data or prose. A reader cannot tell
what terms actually apply to `data/events/` and `paper/`.
**Fix:** add a `LICENSE-DATA` (CC BY 4.0) and state the split ("code: MIT; data and manuscript: CC BY 4.0")
in `LICENSE`, `README.md`, `CITATION.cff` and `data/README.md`.

### B13. The README/data dictionary misdescribe sample size and the UCDP release — MAJOR
`README.md:20,41,42` ("~40 ceasefires", "UCDP GED v24.1"); `analysis/results.json` (36 events, 24 with PAHL,
23 in prediction, GED v26.1). This is the public-facing description of the project and it disagrees with the
data and the analysis. **Fix:** correct to "36 verified events, 24 with a usable PAHL, 23 in the prediction
sample", and to v26.1.

---

## C. MINOR findings

### C1. Greek capital Mu in a bibliography author name — MINOR
`paper/references.bib:342`: "Dean Μ. Krugman" uses U+039C GREEK CAPITAL LETTER MU, not Latin M.
**Fix:** replace with `M`.

### C2. A translated title is presented as the published title — MINOR
`paper/references.bib:735-744` (`murua2017`): the Crossref record is the Spanish original
*"El cese de la violencia como 'bad news': la cobertura del fin de ETA…"*; the bib gives an untranslated-looking
English title. **Fix:** give the original title and add `[Translated title]` or `note = {In Spanish}`.

### C3. Four year mismatches are defensible but should be flagged — MINOR
Crossref records: `candia2019` 2018 online (Nature Human Behaviour 3, 2019 — acceptable);
`clayton2022` published-print 2023 (online 2022); `karakus2017` print 2020 (online 2017);
`downs1972` DOI resolves to a 2016 Routledge reprint. None is fabricated, but a referee checking the DOIs will
see different years; add the online-first/print note or cite the original venue for Downs.
`beardsley2011` resolves to 2017 in Crossref (Cornell UP reissue) — cite the 2011 original explicitly.

### C4. Figure 7 has overlapping annotation/legend text — MINOR
`figures/fig7_placebo_distribution.png`: the annotation "empirical p = 0.9261" collides with the legend entry
"Null study medians (500 draws)". **Fix:** move the annotation or the legend.

### C5. `analysis/results.json` meta field `n_obs` is not "observations" — MINOR
`analysis/pipeline.py:1417` reports `n_obs = panel.diagnostics["n_obs_positive"]` = **1,685,694**, which is
the number of *positive-view* series-days, not the number of observations (the panel has 1,788,776 observed
cells; `pageviews.csv` has 1,736,563 rows including 50,869 zero-view rows). The report labels it "positive
daily observations" correctly (`report.md:28`), but the meta key and manifest are misleading; if the
manuscript quotes it as "daily observations" it will be wrong. **Fix:** rename to `n_obs_positive` and quote
the correct row/observation count in the manuscript.

### C6. The event-study "peak window" differs between code and prose — MINOR
`analysis/pipeline.py:256` searches the pooled peak in [0,+90] days; `src/metrics.py:943-945` searches the
per-series peak in [0,+14]; the manuscript (line 655) says "seven-day-to-thirty-day". Harmonise the text with
the two actual windows.

### C7. The Data section misdescribes title-variant handling — MINOR
`paper/manuscript.md:499-501`: "views to title variants that redirect are not aggregated into the canonical
title". For English they **are** aggregated (`data/README.md`, `en_title_variants.csv`); the limitation applies
to the other 13 editions. **Fix:** say so explicitly, and quantify the fragmentation (see B3).

### C8. The Wikimedia service is misnamed — MINOR
`paper/manuscript.md:463-467` says "Wikimedia Analytics Query Service"; the pipeline uses the Wikimedia REST
**pageviews API** (`.../metrics/pageviews/per-article/...`), not AQS. The bib entry `wikimediaAQS` points at
the AQS docs, which is a different service. **Fix:** cite the pageviews REST API endpoint for the data and keep
AQS out of the data citation.

### C9. Hard-coded absolute paths in generated/user-facing files — MINOR
`data/README.md:6` ("Project root: `/Users/ahmedjaffar/...`"); `analysis/figures_manifest.json` records absolute
paths for every figure. A fresh clone will not match. **Fix:** use repository-relative paths in generated files.

### C10. `degenerate_premean` only flags an exactly-zero baseline — MINOR
`src/metrics.py:1552` flags only `pre_mean <= 0`; `gaza_2021` (0.17) and `gaza_2022` (5.0) pass as
non-degenerate while their thresholds (0.04 and 1.25) are effectively zero. **Fix:** add an absolute floor to
the resumption rule (see A3) and flag thresholds below it.

### C11. `ucdpged` bib entry is stale and versionless — MINOR
`paper/references.bib:706-712`: year 2024, no version/DOI. Given the paper cites a specific release, the
dataset citation should name the version actually used (v26.1) and, ideally, the DOI.

### C12. `paper/manuscript.md` still calls the sample "roughly forty events" — MINOR
`paper/manuscript.md:784`; actual 36 events, 24 with PAHL, 23 in prediction. Replace with the real counts once
Phase 2 is written.

---

## D. Checks that PASS (verified, not assumed)

1. **Data pipeline is reproducible offline.** From the repo root,
   `HTTPS_PROXY=http://127.0.0.1:9 HTTP_PROXY=... .venv/bin/python scripts/run_all.py` completed in 35 s with
   **zero network requests** and exit code 0; SHA-256 of `pageviews.csv`, `ucdp_monthly_country.csv`,
   `ucdp_monthly_dyad.csv`, `ucdp_country_mapping.csv`, `articles.csv`, `seeds.csv` was **bit-identical before
   and after** the re-run. The raw cache is complete for the frozen dataset.
2. **Ceasefire dates verified against sources.** I re-fetched 12 cited URLs and confirmed the recorded date is
   stated on the page: Minsk II 2015-02-15 (ABC: "ceasefire coming into force from February 15"); Syria CoH
   2016-02-27 ("00:00 Damascus time on 27 February"); Ethiopia–Tigray 2022-11-02 ("Pretoria … 2 November
   2022"); Gaza pause 2023-11-24 ("entered into force on 24 November at 7:00"); NK 2020-11-10 ("starting
   12:00 am … November 10, 2020"); Yemen Kuwait 2016-04-10 ("began at midnight, 10 April"); Libya 2020-10-23;
   India–Pakistan 2021-02-25 ("with effect from midnight 24/25 Feb 2021"); Thailand–Cambodia 2025-07-28;
   Gaza 2021-05-21 (TASS "CAIRO, May 21"); DRC–Rwanda 2024-08-04 ("meia-noite de 4 de Agosto de 2024");
   Gaza 2022-08-07 (CGTN dateline "07-Aug-2022" and "Sunday evening"). **No date failed the check.** Caveat:
   a few rows use the article dateline rather than a sentence that states the event date (gaza_2022,
   nk_2023), which is weaker than the method doc's stated standard; note it, don't drop the rows.
3. **Event-table hygiene.** 36 unique `event_id`s, all `event_date` in YYYY-MM-DD, all ISO3 length 3,
   36/36 `verified=TRUE`, no duplicate names, no empty notes/sources; the malformed pre-repair snapshot
   (`ceasefires.raw.csv`, unparsable 16-field line) is preserved and documented in the metadata
   (`provenance_notes`).
4. **Processed-data integrity.** `pageviews.csv`: 1,736,563 rows, 14 languages, 50 articles, 630 series,
   dates 2015-07-01…2025-11-01, zero negatives/nulls/duplicates. UCDP country: 5,782 rows, 101 countries,
   2014-01…2025-12, zero negatives/duplicates; dyad: 20,443 rows/1,049 dyads; mapping 102 rows, unique ISO3,
   PSE→ISR documented. The event→UCDP country proxy is documented in the data dictionary and in code.
5. **Citations are real.** All 65 `references.bib` entries were checked: 58 DOI-bearing entries resolved in
   Crossref and matched title/year (two year conventions noted in C3); the 4 OpenLibrary/Routledge and
   peaceagreements/UCDP/Wikimedia URLs exist (OpenLibrary was slow from this host; the works are the
   well-known books they claim to be). **No fabricated citation.** The two self-reported cuts are confirmed
   absent: there is **no "Jones on hidden emergencies"** entry (the only Jones entry is the real
   Jones & Baumgartner 2005 book) and **no "Kogen 2015"** entry (the only Kogen entry is the real
   Kogen & Price 2011 article, doi:10.1177/1750635211406051).
6. **Code self-tests pass.** `.venv/bin/python analysis/selftest.py` → **15 tests, 0 failures** (PAHL recovery,
   flat/growing rejection, crossing estimator, WPAR/HAC, resumption coding, AUC/logistic, BH-FDR, Cox,
   JSON serialisation, design matrix).
7. **PDF build works.** `.venv/bin/python scripts/build_pdf.py --in paper/manuscript.md --out /tmp/ms_test.pdf`
   → "OK wrote /tmp/ms_test.pdf (165 KB)".
8. **Analysis outputs are internally consistent.** The headline numbers in `analysis/report.md` match
   `analysis/results.json`; I re-derived independently the same PAHL median/IQR (41.80, 29.45–55.70, n = 24),
   WPAR global trend (0.01857, p = 0.0546, ru 4.42 / he 1.64), event-study peak (day 0, half-peak 14),
   resumption base rate (25/33 = 75.8%) and the 24/36 event coverage. The analysis code is seeded and the
   selftest covers the core estimators.
9. **Regression output is honest about its own limits.** `analysis/report.md` §7.1, §7.3, §7.4 and §8 flag the
   placebo failure, the threshold fragility, the 0/8 FDR result and the underpowered prediction. Credit where
   due: the analysis report is a better-quality document than the manuscript currently is. The manuscript must
   not be allowed to smooth these away.

---

## E. Numeric traceability

### E1. Every number currently in the manuscript vs its source

| Manuscript claim (line) | MS value | Source value | Result |
|---|---:|---:|---|
| 14 language editions (22, 326-327) | 14 | `meta.n_languages` 14 | **MATCH** |
| UCDP GED version (545, 597) | 24.1 | data used = 26.1 | **MISMATCH** (A5) |
| placebo pseudo-dates per event (793) | 500 | `PLACEBO_PER_EVENT` 500 | **MATCH** |
| permutation draws (808) | 1000 | `N_PERM` 1000 | **MATCH** |
| resumption threshold (536-538) | 25% | `RESUMPTION_THRESHOLD` 0.25 | **MATCH** |
| pre-window (538) | 6 months | 6 | **MATCH** |
| sustained months (539) | 2 | 2 | **MATCH** |
| follow-up horizon (536) | 12 months | 12 | **MATCH** |
| decay windows (587-588, 806) | 30/90/270 | `PAHL_WINDOWS` | **MATCH** |
| primary fit horizon (492) | 90 (implicit) | `PAHL_PRIMARY_WINDOW` 90 | **MATCH** |
| baseline definition (620) | 28-day rolling mean | fixed [−90,−30] median for PAHL | **MISMATCH** (A4) |
| peak window (655) | [−7,+30]-ish ("seven-to-thirty") | [0,+14] | **MISMATCH** (A4) |
| primary robust estimator (678) | Huber | Theil–Sen | **MISMATCH** (A4) |
| residual offset c (673-677) | estimated | not estimated | **MISMATCH** (A4) |
| residual bootstrap (698) | yes | not implemented | **MISMATCH** (A4) |
| alternative date convention (532) | yes | not implemented | **MISMATCH** (A4) |
| sample size (784) | "roughly forty" | 36 total / 24 PAHL / 23 prediction | **MISMATCH** (B13) |
| "every event has a several-month baseline" (470) | yes | false for 2015 events and 12 excluded | **MISMATCH** (B11) |
| "more than two thousand [ceasefires] 1989–2020" (103) | >2000 | external claim (related_work says 2,202) | OK (not independently re-derived) |

**The manuscript currently contains no Results numbers at all** — the Findings paragraph is `[TK]`. When
Phase 2 is written, every number must be copied from `analysis/report.md`. The main trap is `n_obs` (C5):
1,685,694 is *positive* observations, not total observations.

### E2. Analysis-report headline numbers vs `results.json` (the numbers the manuscript must use)

| Claim in `analysis/report.md` | Report | `results.json` | Result |
|---|---:|---:|---|
| median PAHL (d) | 41.8 | 41.802568 | MATCH |
| IQR | 29.5–55.7 | 29.450383–55.700735 | MATCH |
| bootstrap CI | 31.3–48.4 | 31.322043–48.370402 | MATCH |
| n with PAHL / total | 24/36 | 24/36 | MATCH |
| placebo median (d) | 55.29 | 55.292817 | MATCH |
| placebo one-sided p | 0.926 | 0.926148 | MATCH |
| placebo two-sided p | 0.156 | 0.155689 | MATCH |
| placebo fits / events | 8236 / 24 | 8236 / 24 | MATCH |
| prediction n | 23 | 23 | MATCH |
| positives / negatives | 18 / 5 | 18 / 5 | MATCH |
| OR (95% CI), p | 5.32 (0.74–38.21), 0.096 | 5.3218 (0.7412–38.2085), 0.096464 | MATCH |
| CV AUC (SD) | 0.775 (0.018) | 0.775167 (0.018029) | MATCH |
| LOO predictive AUC | 0.667 | 0.666667 | MATCH |
| permutation p | 0.033 | 0.032967 | MATCH |
| BH-FDR significant | 0 / 8 | 0 / 8 | MATCH |
| Cox HR (95% CI), p | 1.266 (0.831–1.931), 0.273 | 1.266 (0.8305–1.9310), 0.2725 | MATCH |
| WPAR trend / p | 0.0186 / 0.055 | 0.018568 / 0.054561 | MATCH |
| WPAR highest / lowest | ru 4.42 / he 1.64 | 4.4184 / 1.6438 | MATCH |
| resumption base rate | 75.8% (25/33) | 0.757576 (25/33) | MATCH |
| window medians 30/90/270/crossing | 15.7 / 41.8 / 173.5 / 5.5 | 15.7277 / 41.8026 / 173.4727 / 5.5 | MATCH |
| threshold 0.50 OR / CV AUC | 1.66 / 0.587 | 1.6624 / 0.586667 | MATCH |
| event study peak / half-peak | day 0 / day 14 | 0 / 14 | MATCH |

No mismatch was found between `analysis/report.md` and `analysis/results.json`; the analysis stage is
internally traceable. The traceability failure is the manuscript's: it is either `[TK]` or describing a
method that was not run.

---

## F. Statistical-validity notes (why the above matter, concisely)

- **Placebo null.** The null is a same-pipeline random-date null for the same article series, which is the
  right *idea*, but it is conditional on a successful fit (68.6% of placebo draws vs 100% of selected events),
  it is censored at 90 days on both sides, and same-year random dates in conflict-dense years pick up other
  escalations. The report acknowledges the last point and calls its test conservative. The conclusion is still
  a null; the paper cannot claim event-specificity.
- **Permutation test.** Correctly permutes the outcome with X fixed, two-sided, ridge-penalised, +1 correction.
  It is valid as a test of association; it is simply one of eight tests and does not survive FDR.
- **AUC.** The manuscript (as written) promises cross-validated and in-sample AUC side by side, and the analysis
  delivers both (0.775 CV, 0.800 in-sample, 0.667 LOO). That is the right practice. But 5 negative events means
  the AUC is coarse and unstable; the intervals are not reported for CV AUC (only SD across repeats, which is a
  stability measure, not a sampling interval). Add a bootstrap/CI for the CV AUC or explicitly say it cannot be
  estimated.
- **Threshold sensitivity.** The 50% variant halves the effect (OR 1.66, AUC 0.587). This is the single most
  important robustness result after the placebo and belongs in the abstract, not only in §7.3.
- **p-hacking.** The analysis does the right thing (pre-specified checks, FDR, LOO, permutation); the risk is
  purely in how the manuscript selects what to headline. Report 0/8 and the null survival model prominently.
- **n disclosure.** The analysis discloses n everywhere; the manuscript must carry 24/36 (PAHL) and 23
  (prediction) into the abstract and every coefficient sentence, not "roughly forty".

---

## G. Verdict

**Not submittable, in its current state, by a wide margin.**

The data engineering is the strongest part of the project and is genuinely reproducible offline (OK). The
ceasefire dates are correct (OK, 12 spot-checks). The citations are real (OK, 65 checked; 4 syntax errors to
fix). The analysis report is unusually honest about its own failures (OK). But three of the paper's load-bearing
claims fail on its own terms:

1. **The placebo test fails** — the measure is not shown to be event-specific, which is the paper's first and
   central claim. The paper must be re-framed as reporting that null (the 41.8-day figure is not a validated
   half-life).
2. **The half-life is estimator-dependent by a factor of ~30** (5.5 vs 41.8 vs 173.5 days; event-study
   half-peak 14 days), and 23% of fits are right-censored at the window. The headline number is not a stable
   measurement.
3. **The only positive result (PAHL → resumption) rests on 23 events with 5 negatives, a contaminated outcome
   (event-month and country-level contamination; at least four coded "resumptions" are arguably false), a null
   survival model, 0/8 after FDR, and a result that disappears at the 50% threshold.** It is an exploratory
   association at best, not an "early-warning lead indicator".

In addition, the Methods section describes a different estimator from the one that was run, and the paper
cites UCDP GED v24.1 while every number comes from v26.1 — both are the kind of error that gets a preprint
rejected or, worse, published and then retracted.

**Minimum changes before any public preprint:** (i) fill Results/Discussion and remove all `[TK]`; (ii) correct
GED to v26.1; (iii) rewrite Methods to match code; (iv) re-frame around the placebo null and the
estimator-dependence, with the censoring/survival treatment of PAHL; (v) fix or clearly bound the resumption
coding (post-window start, absolute floor, conflict-specific series) and report the corrected base rate and
sensitivity; (vi) report FDR (0/8), the survival null, the 50%-threshold sensitivity and the n = 23/5-negative
constraint in the abstract; (vii) add Oswald & Ohrenhofer (2022) and the Reynal-Querol et al. attention-decay
work and narrow the novelty claim; (viii) fix the four BibTeX commas, the GED version, the Makefile targets and
the licence split. Then the paper would be a modest, honest descriptive note (Wikipedia attention spikes and
decays around ceasefire announcements; the decay parameter is not event-specific at this sample size) rather
than the early-warning paper the abstract currently promises.

*This review was written from the frozen inputs and analysis outputs at 2026-11-08T03:08Z; the manuscript was
last modified 2026-11-07T21:59 local and still contained no Results/Discussion at review cutoff.*

---

## Addendum: re-audit of the final manuscript (2026-11-07 late)

*Supersedes the tags above; re-audited against the final `paper/manuscript.md` (sha256 `5380763…`, 0 `[TK]`) and
`analysis/results.json`/`report.md`.*

**1. Is it submittable now? Yes, after the fixes below.**
- **A1 (decay placebo): YES, remediated.** The abstract, §5.4, §5.6, §6, §7 and §8 all report the null
  (p = 0.926 / 0.156; 0 of 24 events) and no text claims event-specific decay. One residue: the abstract says
  "estimate it for 36 verified ceasefires" — change to **"for 24 of 36"** (only 24 estimates exist).
- **A2 (window sensitivity): YES, adequately disclosed** (§4.4, §5.7, §7: 15.7 / 41.8 / 173.5 days at
  30 / 90 / 270 days; 5.5 days crossing; rank correlations 0.59 / 0.35). Add "under the 90-day censoring
  window" to the abstract's 41.8; drop "lower bound" from the Figure 2 caption.
- **B1 (FDR / survival null): YES** — 0 of 10 tests after BH, Cox null, n = 23 with 5 non-resumptions all reported.
- **B2 (50% threshold): YES** — the attenuation is reported in Results, Discussion and Limitations.
- **B7 (war/peace falsification): YES for disclosure** — §4.8/§5.3 state the condition is met. But delete or
  qualify the Discussion sentence *"War attracts more attention and sheds it faster; peace attracts less and
  keeps it longer"*: the paper's own paired difference is 0.0 days (CI −14.7 to 6.2), i.e. no distinguishable
  difference. Also delete "with the same covariates" and "a proportional-hazards check" from the Cox paragraph —
  the model is single-covariate and no PH check was run.

**2. B4 worst offenders** (event_id → current article → should be):
- `india_pak_2025` → "Insurgency in Khyber Pakhtunkhwa" → **"2025 India–Pakistan conflict"** (or "Kashmir
  conflict"). This is the only wrong-conflict mapping that contributes a PAHL (31.3 d). Fix or drop.
- `philippines_2016` → "Philippine drug war" → **"Communist rebellion in the Philippines"** (excluded from
  PAHL; fix or drop).
- `myanmar_nca_2015` → "Myanmar civil war (2021–present)" → **"Internal conflict in Myanmar"** (excluded; the
  2021 article post-dates the 2015 event).
- `gaza_2021`, `gaza_2022` → "Gaza war" → **"2021 Israel–Palestine crisis"**, **"2022 Gaza–Israel clashes"**.
  "Gaza war" was a low-traffic redirect then (English = 431 views in May 2021); remap or drop these two.
- `israel_iran_2025`, `thai_camb_2025` → unmapped → "Israel–Iran conflict (2025)", "Cambodian–Thai border
  dispute"; both currently contribute no PAHL.

**3. B10 — the four BibTeX entries:** `@book{jones2005}` (`paper/references.bib:678`), `@book{baumgartner1993}`
(:686), `@book{fortna2008}` (:694), `@book{moeller1999}` (:702) each lack the comma after `year = {...}` before
`url = {...}`. Fix: `year = {2005},` etc. — four one-character edits.

**4. B5 — single most damaging uncited paper:** **Oswald, C. & Ohrenhofer, D. (2022), "Click, click boom: Using
Wikipedia data to predict changes in battle-related deaths", *International Interactions* 48(4),
doi:10.1080/03050629.2022.2061969.** It uses Wikipedia pageviews as a conflict-salience measure to predict battle
deaths, directly contradicting "What pageviews have not been used for … is attention to armed conflict"
(ms ~line 135) and "which to our knowledge has not been done" (~line 149). Cite it and narrow the claim.

**5. Residual risk (one sentence):** the **resumption outcome** — its 12-month post window starts in the event
month and uses country-level totals, so Gaza 2021/2022, Colombia 2016 and India–Pakistan 2021 are demonstrably coded "resumed" from
pre-ceasefire or other-conflict violence; re-coding those four events drops OR from 5.32 to 2.40 and CV AUC
from 0.775 to 0.634. Secondarily, the spike subsection's claim that a near-zero correlation "rules out
regression to the mean" is unsupported: it is computed on observed events, not placebo draws, and its CI
spans −0.43.
