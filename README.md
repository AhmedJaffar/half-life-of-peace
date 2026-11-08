# The Half-Life of Peace

**How long does the world look at a ceasefire before it looks away?**

A computational study of public attention to ceasefires, 2015–2025, measured across **14 Wikipedia
language editions**, joined to **36 verified ceasefire events** and to georeferenced conflict
fatalities from the **Uppsala Conflict Data Program (GED 26.1)**.

📄 **Manuscript:** [`paper/manuscript.pdf`](paper/manuscript.pdf) · [`paper/manuscript.md`](paper/manuscript.md)
🔁 **Reproduce:** `make all` (data → analysis → figures → PDF)

---

## What we found

**1. There is a half-life, and it is about six weeks.**
Attention to a ceasefire spikes on the announcement day and decays with a median half-life of
**41.8 days** (IQR 29.5–55.7; bootstrap 95% CI 31.3–48.4; n = 24 of 36 events). Mean excess attention
peaks on day 0 (0.489 log units) and reaches half its peak by day 14.

**2. But the decay rate is not ceasefire-specific — this is a null result, and we report it as one.**
The same estimator applied at 500 random dates per event yields a *longer* median half-life
(55.3 days). One-sided empirical **p = 0.926**, two-sided p = 0.156, and **0 of 24 events** beats its
own placebo null at p ≤ 0.05. PAHL is therefore best read as the *attrition schedule of attention to
conflict content*, not as a property of peace processes.

**3. The world reads about war far more than about peace.**
The War–Peace Attention Ratio (WPAR) is **2.65** globally — war-concept articles draw 2.65× the views
of peace-concept articles. It is highest in the Russian edition (**4.42**) and lowest in Hebrew
(**1.64**), with a weak upward trend of 0.0186 log units/year (95% CI −0.0004 to 0.0375; p = 0.055).

**4. The predictive signal is exploratory and we do not claim it.**
A one-SD longer half-life is associated with higher odds of violence resumption (OR **5.32**, 95% CI
0.74–38.21; p = 0.096; CV AUC 0.775), but the interval is compatible with no effect, only **5 events**
did not resume, leave-one-out AUC falls to 0.667, and **nothing survives FDR correction**. A larger
announcement spike points the *opposite* way (OR 0.318, 95% CI 0.100–1.012; p = 0.052).

> **The one-sentence version.** The world stops paying attention to a ceasefire on roughly the same
> six-week schedule on which it stops paying attention to anything else — and that schedule does not
> reliably predict which ceasefires hold.

## Why this is new

The decay estimator is **not ours** — it is the collective-attention framework of Candia et al.
(2019, *Nature Human Behaviour*), transferred to a new event class. The outcome logic is **not ours** —
it is adopted from Clayton & Sticher (2021, *ISQ*), who model ceasefire survival on UCDP GED deaths.
What is new is (a) estimating an attention half-life for ceasefire announcements at all, (b) testing
the decay *rate* — not the level — as an ex-ante predictor, (c) the cross-lingual War–Peace Attention
Ratio, and (d) the first use of Wikipedia pageviews for conflict attention. See
[`paper/related_work.md`](paper/related_work.md) for the verified gap analysis and
[`paper/gap_risks.md`](paper/gap_risks.md) for the objections we expect.

## Data

| Source | Content | Coverage |
|---|---|---|
| [Wikimedia pageviews API](https://wikimedia.org/api/rest_v1/) | Daily views, article × language | 2015-07-01 → 2025-11-01 |
| Curated ceasefire table (this repo) | 36 verified agreements, 20 countries | 2015–2025 |
| [UCDP GED v26.1](https://ucdp.uu.se/downloads/) | Georeferenced fatalities → monthly | 2014-01 → 2025-12 |

- **1,736,563** pageview rows · **630** article–language series · **50** conflict articles · **14** languages
- Article titles in each language are resolved **programmatically** via MediaWiki `prop=langlinks`, not
  hand-translated, so the multilingual construction is auditable.
- GED codes event *location*, so Gaza/West Bank events appear under Israel; the join is made through an
  explicit, documented mapping table (`data/processed/ucdp_country_mapping.csv`).

## Reproduce

```bash
git clone https://github.com/AhmedJaffar/half-life-of-peace
cd half-life-of-peace
make all          # venv + data -> analysis -> figures + PDF   (~10-15 min first run)
```

Every HTTP response is cached under `data/raw/`; a re-run needs **zero network requests** and takes
about 20 seconds for the data stage and ~65 seconds for analysis + figures.

Verify that every number quoted in the paper traces to `analysis/results.json`:

```bash
make check        # scripts/verify_claims.py — fails on any untraceable number or [TK]
```

## Layout

```
src/          pipeline modules (seeds, langlinks, pageviews, ucdp, metrics, models)
scripts/      run_all.py · build_pdf.py · verify_claims.py
data/events/  36 verified ceasefires + provenance      (committed)
data/         raw + processed data                     (gitignored, regenerated)
analysis/     results.json, report.md, tables/         (generated)
figures/      10 figures at 300 dpi, PNG + PDF         (generated)
paper/        manuscript, related work, gap risks, review, submission playbook
docs/         events method note
```

## Citation

```bibtex
@misc{jaffar2026halflife,
  author = {Jaffar, Ahmed},
  title  = {The Half-Life of Peace: Multilingual Measurement of Public Attention
            Decay After Ceasefires, 2015--2025},
  year   = {2026},
  note   = {Preprint. Code: https://github.com/AhmedJaffar/half-life-of-peace}
}
```

## Honest limitations

- Wikipedia pageviews are a proxy for attention and over-represent literate, online populations.
- 36 events, 24 with a fitted half-life; the predictive analysis (n = 23, 5 non-resumptions) is
  **exploratory and underpowered**, not confirmatory.
- The half-life estimate is strongly window-dependent (15.7 / 41.8 / 173.5 days at 30/90/270-day
  windows; 5.5 days for a non-parametric crossing estimator). We report the sensitivity in full.
- No causal identification is claimed anywhere.

## License

Code: MIT. Data and manuscript: CC BY 4.0.
