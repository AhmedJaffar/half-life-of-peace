# The Half-Life of Peace

**A multilingual, event-based measurement of public attention decay after ceasefires, 2015–2025**

Design document v1 · 2026-11-07 · Lead

---

## 1. The question

When a ceasefire is announced, the world looks. How long does it keep looking — and does how quickly it looks away tell us whether the ceasefire will hold?

We ask three linked questions:

1. **Measurement.** How fast does global public attention to a conflict decay after a ceasefire is announced? We introduce the **Peace Attention Half-Life (PAHL)**: the number of days for attention to fall to half its post-announcement peak.
2. **Structure.** Does attention to *peace* concepts decay faster than attention to *war* concepts? We introduce the **War–Peace Attention Ratio (WPAR)** to measure this at language and global scale.
3. **Prediction.** Is a longer attention half-life associated with a ceasefire surviving its first year?

---

## 2. Why this has not been done

The issue-attention cycle (Downs 1972) predicts that public attention to any crisis rises, peaks, and decays — but it was theorised for domestic policy issues and has never been operationalised as a *measurable half-life* for international peace processes.

Conflict forecasting has become a mature field (UCDP, ViEWS, ACLED-based early warning), but it is overwhelmingly **violence-side**: models consume event counts, fatalities, and structural covariates. The **attention side** — how much the world is actually watching — is treated as a mediator at best, never as a measurable leading indicator.

Meanwhile the peace-durability literature (Fortna 2004; Beardsley 2011; Kreutz 2010; Hultman et al.) explains ceasefire survival using agreement design, third-party guarantees, and power-sharing. It does not consider whether *sustained public attention* is part of the enforcement mechanism — even though attention is precisely what generates the political cost of violation.

The gap: **no study has (a) defined and estimated an attention half-life for peace processes, (b) done so across language editions at global scale, or (c) tested whether that half-life carries predictive information about ceasefire survival.** The three datasets needed — multilingual pageview time series, a verified ceasefire event table, and georeferenced conflict fatalities — have never been joined for this purpose.

---

## 3. Data

| Source | Content | Resolution | Coverage |
|---|---|---|---|
| Wikimedia pageviews API | Daily article views per language edition | daily × article × language | 2015-07 to 2025-11 |
| Curated ceasefire table | Verified ceasefire/agreement events | event | 2015–2025 |
| UCDP GED v24.1 | Georeferenced conflict fatalities | event → monthly | 2014–2025 |

**Concept families.** WAR: War, Armed conflict, Civil war, Invasion, Airstrike, Genocide, Terrorism, Military occupation, Refugee, War crime. PEACE: Peace, Ceasefire, Peace treaty, Peacebuilding, Mediation, Diplomacy, Reconciliation, Disarmament, Demobilization, Peacekeeping, Humanitarian aid.

**Languages (14).** en, ar, es, fr, de, ru, zh, fa, tr, id, pt, uk, he, hi — chosen to span the theatres of the covered conflicts and the global mediator/donor states.

Article titles in each language are resolved **programmatically via MediaWiki `prop=langlinks`**, not hand-translated, so the pipeline is auditable and reproducible.

---

## 4. Measures

**Excess attention.** For article $a$, language $\ell$, day $t$:

$$E_{a,\ell,t} = \log(1+\text{views}_{a,\ell,t}) - \text{baseline}_{a,\ell,t}$$

where baseline is a 28-day centred rolling mean, computed excluding a ±14-day window around the event to avoid contamination.

**PAHL.** On the post-peak decay window, fit $E_t = A e^{-\lambda t}$ by robust log-linear regression; $\text{PAHL} = \ln 2 / \lambda$ days.

**WPAR.** Monthly, per language: $\text{WPAR}_{\ell,m} = \sum_{a\in\text{WAR}} \text{views} \;/\; \sum_{a\in\text{PEACE}} \text{views}$.

**Resumption.** A ceasefire fails if, within 12 months after the event, monthly fatalities in the theatre country exceed 25% of the 6-month pre-event mean for at least two consecutive months. (Threshold varied in robustness.)

---

## 5. Analysis plan

1. **Event study** — align all ceasefires at $t=0$, aggregate excess attention over $[-90,+365]$, locate peak and die-off.
2. **PAHL estimation** — per event, per family, per language; bootstrap CIs; distributional summary.
3. **WPAR trend** — 2015–2025 with HAC standard errors; seasonal decomposition; cross-language dispersion.
4. **Prediction** — logistic regression of resumption on standardized PAHL + controls; AUC with cross-validation; Cox survival variant. Framed as **exploratory**.
5. **Robustness** — placebo dates (500/event), alternative windows and thresholds, leave-one-out, permutation tests, English-only sensitivity.

---

## 6. What would falsify this

- PAHL is indistinguishable from the placebo-date distribution → attention decay is not event-specific, and the measure is meaningless.
- PAHL shows no association with resumption after permutation → no predictive claim survives; report as null.
- Attention to PEACE concepts decays *slower* than WAR concepts → the "peace attention deficit" framing is wrong and must be reversed.

All three are reported whichever way they fall.

---

## 7. Limitations (stated up front)

- Wikipedia pageviews are a proxy for attention, skewed toward literate, online populations. Not equal to public opinion.
- n ≈ 40 events; prediction analysis is underpowered and exploratory. No causal claim is possible.
- Ceasefire designation requires curation judgment; inclusion criteria are documented but not beyond dispute.
- Confounding: attention and violence both respond to underlying conflict dynamics; we control for pre-event violence but cannot claim identification.

---

## 8. Deliverables

Reproducible pipeline · frozen datasets · manuscript (PDF) · submission package for preprint servers (arXiv/SSRN/Zenodo DOI) + ResearchGate · submission playbook for Google Scholar indexing.
