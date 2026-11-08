# Gap Risks: The Five Strongest Objections to Our Novelty Claim
### "The Half-Life of Peace"

*Candid adversarial review of the gap statement in `related_work.md` §5. For each objection: why it bites, how to defend, what to concede, and the specific writing move that neutralises it. Written by the literature scout; deliberately harsh, because a reviewer will be.*

---

## Objection 1 — "Attention decay is not new. Candia et al. (2019) already established a universal decay law; you are running their estimator on a new list of events. That is a replication, not a contribution."

**Why it bites.** This is the objection most likely to be fatal at review, because it is substantially correct as stated. The measurement machinery for PAHL — bi-exponential decay, fast "communicative" and slow "cultural" half-lives, the half-life as a summary parameter — is fully developed in Candia et al. (2019), with Lorenz-Spreen et al. (2019) on acceleration, Parolo et al. (2015) on field variation, and Pfeffer and Matter (2023) on half-life estimation for a single platform. A reviewer who knows this literature will ask what remains.

**How to defend.** The novelty must be located in the *object* and the *test*, never in the estimator. Three specific claims survive:
1. **A new event class with an observable political outcome.** Candia et al. treat cultural items (biographies, music, films) whose "outcome" is continued consumption. A ceasefire is an event whose *survival* is independently measured by UCDP GED. That makes it possible to ask a question the decay literature structurally cannot ask: does the shape of the decay curve predict whether the underlying process persists?
2. **The rate as a predictor, not a description.** Every paper in the decay literature treats the decay rate as a dependent variable or a descriptive parameter. We treat it as an *ex ante covariate* for a political outcome. That is a different statistical role, not a new curve.
3. **Cross-lingual variation as a substantive variable.** Candia et al. pool across sources; we estimate PAHL separately in ~12 language editions, which turns the decay rate into a *varying* quantity that can be related to which publics are paying attention. No prior work does this for any event class.

**What to concede.** Explicitly, in the paper: "PAHL is not a new estimator; it is the first application of an established bi-exponential decay estimator to ceasefire announcements." Do not use the word "novel" for the metric. Use "novel" only for the *predictive test* and the *cross-lingual design*.

**Writing move.** Put a sentence in the introduction of the form: *"We adopt rather than propose the decay estimator of Candia et al. (2019); our contribution is what the resulting rate predicts."*

---

## Objection 2 — "Wikipedia page views are not public attention. They measure the curiosity of a self-selected, disproportionately young, male, English-reading, online encyclopaedia audience, and you never validate the construct against any measure of conflict salience."

**Why it bites.** This is the deepest threat, because it attacks the measurement instrument rather than the contribution. The supporting literature cuts both ways: Yasseri and Bright (2016) are explicit that using page views as a public-attention proxy requires assumptions that are rarely tested; Ruprechter et al. (2023) show that Wikipedia attention is systematically skewed by wealth and region, so cross-lingual comparisons may partly measure *who has broadband*, not *who cares*; and the page-view series can be driven by bots, mirroring, and search-engine ranking changes.

**How to defend.** Partial defence only, and we should take it:
1. **Relabel the construct.** Call it "Wikipedia attention" or "online encyclopaedic attention", not "public attention". This costs us rhetorical punch and buys us immunity from a class of objections.
2. **Triangulate on a subsample.** For 3–5 ceasefires, correlate the Wikipedia series with Google Trends and (if available) newspaper counts from a media archive. If the correlations are high, the construct travels; if low, we report it and bound our claims. This is a small, cheap robustness section that pre-empts the objection.
3. **Leverage the cross-lingual design as a feature.** The fact that page views exist for ~12 editions with consistent definitions is precisely what makes cross-lingual comparison possible; no other attention source has that coverage for 2015–2025.

**What to concede.** We cannot claim to measure "public opinion" or "salience" in any survey sense. We must say so, and we must not generalise beyond Wikipedia's readership. If the triangulation fails, the paper's claim shrinks to "Wikipedia attention predicts…", which is still publishable but weaker.

**Writing move.** A dedicated Limitations paragraph beginning: *"Page views are a measure of one particular kind of attention…"* — and cite Ruprechter et al. (2023) ourselves rather than letting a reviewer do it.

---

## Objection 3 — "The causal story is backwards. Attention falls because the ceasefire is *working*. A boring, stable peace generates no page views. So low attention should predict durability, not collapse — and your headline finding may have the wrong sign."

**Why it bites.** This is a genuine theoretical objection, not a methodological quibble, and it is the one most likely to sink the paper's narrative if unaddressed. Ceasefires that hold produce no dramatic news; ceasefires that collapse produce a spike of attention. A negative association between attention decay and collapse is therefore at least as plausible as a positive one, on pure news-value grounds (Galtung and Ruge, 1965).

**How to defend.**
1. **Pre-register a directional hypothesis and state the competing mechanisms explicitly.** There are two, and they make opposite predictions: (a) *accountability/monitoring* — sustained attention raises the cost of defection and predicts durability; (b) *salience/severity* — attention tracks violence, so an attention spike after announcement (not decay) predicts breakdown. Present both, and let the data adjudicate. A paper that predicts a sign and tests it is far stronger than a paper that reports whatever sign appears.
2. **Separate level from rate.** The decay-rate claim is not the same as the level claim: two ceasefires can have identical announcement-day attention and very different half-lives. If the *rate* carries information net of the *level*, that is a substantive finding and cannot be explained by "boring peace" alone.
3. **Control for the obvious confounders.** Violence intensity at announcement (UCDP GED), conflict salience (total page views across the conflict's article set), ceasefire type from the ETH/PRIO CF dataset (Clayton et al., 2022), number of signatories, and whether the ceasefire is local or national.

**What to concede.** We cannot identify a causal effect from an observational panel. Say "predicts", never "causes". Present out-of-sample predictive performance (following Ward et al., 2010, and ViEWS conventions) rather than a causal coefficient.

**Writing move.** A short "Competing expectations" subsection in the theory section, with an explicit sign prediction and a stated falsification condition.

---

## Objection 4 — "The outcome is not new, either. Clayton and Sticher (2021) already model ceasefire survival using UCDP georeferenced deaths; Lundgren et al. (2023) already estimate ceasefire effects on violence intensity. Once you strip the attention variable, your paper is 'the same model with one extra covariate.'"

**Why it bites.** Because it is true, and because we cannot claim otherwise. Clayton and Sticher (2021) build survival models of ceasefires with PA-X provisions and UCDP GED deaths; Lundgren et al. (2023) run interrupted time series and spatial panels on 145 Syrian local ceasefires. Our outcome is their outcome.

**How to defend.** Reframe the contribution from "new explanation of durability" to **"a new class of ex ante lead indicator for early warning."** This is a real and defensible distinction:
- Structural predictors in the durability literature (power-sharing, peacekeeping, mediation, troop levels) are largely **known only after** the settlement is designed and implemented. They are excellent for explaining durability in retrospect and weak as real-time warning.
- Attention decay is **observable in near-real time, from public data, at announcement**, in every language, for every ceasefire — including ceasefires in conflicts with no peacekeeping mission and no media presence in the Global North.
- That is precisely the gap that the early-warning literature cares about (Chadefaux, 2014; Hegre et al., 2019), and it is not filled by any existing covariate.

**What to concede.** Incrementality. Say plainly: "we add a predictor, not a theory of durability." Do not claim to explain *why* ceasefires fail.

**Writing move.** One paragraph positioning the paper in the early-warning tradition rather than the durability tradition, with ViEWS and Chadefaux cited as the evaluation standard.

---

## Objection 5 — "A single exponential half-life is the wrong functional form. Attention after a ceasefire will be multimodal — an announcement spike, violation-driven spikes, anniversary effects, and a long tail — so your fit will be mis-specified and your half-life estimates unstable across reasonable windows."

**Why it bites.** It is almost certainly right. Ceasefire attention is not a clean decay process: Gaza, Ukraine and Syria generate repeated shocks, and García-Gavilanes et al. (2017) show that commemoration reactivates attention to past events — a mechanism that directly violates a monotone decay assumption. Pfeffer and Matter (2023) show that half-life estimates are sensitive to the operational definition, which means our numbers could move substantially with window choice.

**How to defend.**
1. **Use the bi-exponential form, not a single exponential.** Candia et al. (2019) already show that two components are needed; adopting their form is both more defensible and rhetorically stronger ("we follow the established specification").
2. **Pre-register the window and the exclusion rule.** Define the observation window (e.g. 90 days post-announcement), and specify in advance how violation-driven spikes are handled — either modelled explicitly as exogenous shocks or excluded by a stated rule. Report results under at least three window definitions.
3. **Report uncertainty and instability honestly.** Bootstrap the half-life; report the distribution, not a point estimate; show the sensitivity table. A paper that reports "PAHL is unstable, and here is exactly how" is more credible than one that reports a tidy number.
4. **Consider a hazard/functional-data framing** as a robustness check rather than forcing everything through a single scalar.

**What to concede.** The scalar half-life is a lossy summary. Present it as a descriptive summary with an explicit error bar, and consider reporting the full fitted curve as the primary object with PAHL as a convenience.

**Writing move.** A methods subsection titled "Why two components, and how sensitive the half-life is" — turning the objection into a demonstration of care.

---

## Secondary objections worth pre-empting in a footnote or appendix

- **Case selection.** Why 35–45 ceasefires rather than the 2,202 in the ETH/PRIO CF dataset (Clayton et al., 2022)? Answer: we require a mappable conflict-specific Wikipedia article set and sufficient page-view volume. Report the inclusion rule and show the excluded cases do not differ systematically on observable durability.
- **Language-edition selection.** ~12 editions is a convenience sample weighted toward large Wikipedias. Report readership sizes and test whether results are driven by English, Russian and Arabic.
- **Article-set construction is a researcher degree of freedom.** Fixing the war-concept and peace-concept article lists is a place where results could be tuned. Pre-register the lists (or derive them by a documented rule, e.g. Wikidata-based concept selection as in Gildersleve and Lambiotte, 2023) and publish them.
- **Multiple comparisons across ~40 ceasefires × 12 editions.** Pre-specify the primary specification and treat the rest as exploratory; use hierarchical shrinkage rather than per-cell tests.
- **"So what?"** If the finding is real, what follows? The honest answer is "a cheap, real-time monitor", not "a policy lever". Claiming the latter would invite the reply that attention is a symptom, not a cause — see Objection 3.

---

## The fallback claim (use this if pressed hard)

If a reviewer rejects the causal framing and the novelty of the metric, the paper still has a defensible core:

> *We provide the first measurement of how quickly attention to ceasefires decays, across twelve language editions and forty agreements, and we show whether that decay is associated with the resumption of violence. Even if the association is null, the measurement itself is new and the null is informative: it would establish that attention dynamics carry no information about ceasefire survival, which is a useful negative result for the early-warning literature.*

That claim is modest, true, and survives all five objections. It should be the floor of the paper, not the ceiling.
