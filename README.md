# The Half-Life of Peace

**How long does the world look at a ceasefire before it looks away?**

A computational study of public attention to ceasefires, 2015–2025, measured across 14 Wikipedia
language editions, joined to a verified ceasefire event table and to georeferenced conflict
fatalities from the Uppsala Conflict Data Program.

> **Status:** research in progress. Numbers in this README are generated from
> `analysis/results.json`; see `paper/manuscript.md` for the full write-up.

---

## The idea in one paragraph

The issue-attention cycle says public attention to a crisis rises, peaks, and fades. Nobody has
turned that intuition into a *measurable quantity* for international peace processes, or asked
whether the rate of fading carries information about whether the peace survives. This project
defines the **Peace Attention Half-Life (PAHL)** — the number of days for attention to a ceasefire
to fall to half its post-announcement peak — estimates it for ~40 ceasefires across 14 languages,
and tests whether it is associated with the ceasefire collapsing within 12 months.

It also defines the **War–Peace Attention Ratio (WPAR)**: how much more attention the world pays
to war than to peace, per language, per month.

## Why it is new

- Conflict forecasting is violence-side (event counts, fatalities). This is **attention-side**.
- The peace-durability literature models agreement design and guarantees, not **enforcement via
  sustained scrutiny**.
- No prior work has estimated an attention *half-life* for peace processes, done it across
  language editions, or tested it against conflict recurrence.

See [`paper/related_work.md`](paper/related_work.md) for the verified gap analysis.

## Data

| Source | What | Access |
|---|---|---|
| Wikimedia pageviews API | Daily views, article × language | public, no key |
| Curated ceasefire table | ~40 verified agreements 2015–2025 | in this repo, `data/events/` |
| UCDP GED v24.1 | Georeferenced fatalities | public download |

Article titles in each language are resolved **programmatically** via MediaWiki `prop=langlinks` —
not hand-translated — so the multilingual construction is auditable.

## Reproduce

```bash
git clone https://github.com/AhmedJaffar/half-life-of-peace
cd half-life-of-peace
make all          # venv + data + analysis + figures + paper
```

Records take a few minutes; pageview and GED downloads are cached and resumable.

## Layout

```
src/          pipeline modules (seeds, langlinks, pageviews, ucdp, metrics, models)
scripts/      run_all.py orchestration, verify_claims.py
data/events/  curated ceasefire table + provenance  (committed)
analysis/     results.json, tables/, report.md      (generated)
figures/      publication figures, 300 dpi           (generated)
paper/        manuscript, bibliography, gap analysis (committed)
docs/         methods notes
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

## License

Code: MIT. Data and manuscript: CC BY 4.0.

## Honest limitations

Wikipedia pageviews are a proxy for attention and over-represent literate, online populations.
n ≈ 40 ceasefires; the predictive analysis is **exploratory and underpowered**, not confirmatory.
No causal claim is made.
