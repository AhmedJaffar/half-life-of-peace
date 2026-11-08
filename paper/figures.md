# Figure index

Ten figures are produced by `analysis/figures.py` at 300 dpi, in both PNG and
PDF, and written to `figures/`. The manuscript embeds the PNG versions with
relative paths (`../figures/<name>.png`); the PDF versions are identical vector
output and are the ones to use for print submission.

All figures are generated from `analysis/results.json` and the frozen inputs
listed in `analysis/manifest.json`, with a fixed random seed, so they regenerate
deterministically with `make figures` (or
`.venv/bin/python analysis/run.py --stage figures`). No figure is hand-edited.

| # | File (PNG / PDF) | Embedded in | Caption |
|---|---|---|---|
| 1 | `figures/fig1_attention_response.png` / `.pdf` | Results, event study | Mean excess attention around ceasefire announcements, aligned at day 0, across language editions and events (n = 34 events). Two series are plotted: the unsmoothed daily cross-event mean (0.694 at day 0) and the 7-day centred median used for peak detection (0.503 at day 0, half-peak at day 13). Shading is a 95 per cent confidence band across events. |
| 2 | `figures/fig2_pahl_distribution.png` / `.pdf` | Results, PAHL distribution | Distribution of event-level PAHL estimates (n = 24 events). The histogram is right-skewed and censored at the ninety-day fitting window, so the median is a lower bound on the true typical half-life. |
| 3 | `figures/fig3_pahl_vs_resumption.png` / `.pdf` | Results, prediction | Event-level PAHL against resumption of violence within twelve months (n = 23 events; 18 resumed, 5 did not). The direction is that longer-lived attention accompanies more resumption, the opposite of the enforcement expectation, but the groups overlap heavily. |
| 4 | `figures/fig4_wpar_timeseries.png` / `.pdf` | Results, WPAR | Monthly War-Peace Attention Ratio by Wikipedia language edition, 2015-2025 (14 editions, 125 months). The ratio is war-basket views divided by peace-basket views; the horizontal position of each series reflects its level, and the spread across editions is substantial. |
| 5 | `figures/fig5_event_heatmap.png` / `.pdf` | Results, event study | Event-level heatmap of excess attention by event and day relative to the announcement, ordered by event date. The magnitude of the announcement spike and the speed of its decay vary widely across events, which is why the pooled curve is not a typical case. |
| 6 | `figures/fig6_regional_pahl.png` / `.pdf` | Results, PAHL distribution | Median PAHL by region. Regional estimates rest on a few events each and are descriptive rather than comparative. |
| 7 | `figures/fig7_placebo_distribution.png` / `.pdf` | Results, placebo test | Placebo distribution of PAHL from 8236 fits at random same-year dates (light) against the observed event-level distribution (dark). The observed median of 41.8 days is shorter than the placebo median of 55.3 days, so the ceasefire-specific claim fails. |
| 8 | `figures/fig8_roc_prediction.png` / `.pdf` | Results, prediction | ROC curves for the exploratory prediction models, comparing in-sample and repeated cross-validated performance. The gap between the two is the optimism of the in-sample fit. |
| 9 | `figures/fig9_language_pahl.png` / `.pdf` | Results, PAHL distribution | Event-level PAHL estimates by language edition. Each point is a fitted half-life for one event in one edition; editions with few fitted series contribute correspondingly noisy estimates. |
| 10 | `figures/fig10_robustness.png` / `.pdf` | Results, robustness | Sensitivity of the PAHL median and of the predictive AUC to alternative decay windows, resumption thresholds and leave-one-out deletion. |

## Notes for the build

- The manuscript's PDF build (`scripts/build_pdf.py`) resolves image paths
  relative to `paper/`, which is why the embeds use `../figures/...`.
- Figures are wide relative to the A4 text block; the build scales them to the
  content width and caps height at 105 mm, so a figure never breaks a page
  layout.
- Figure 9 is the tallest of the set and occupies most of a page. If a shorter
  build is needed, it is the natural candidate to move to supplementary
  material ahead of Figure 6.
- The three figures that carry the paper's argument are Figure 1 (the spike),
  Figure 7 (the failed placebo), and Figure 4 (the war-peace ratio). If the
  release is announced with images, those are the three.
