---
title: "The Half-Life of Peace: Multilingual Measurement of Public Attention Decay After Ceasefires, 2015-2025"
author: "Ahmed Jaffar"
date: "2026-11-07"
keywords:
  - peace and conflict studies
  - ceasefire durability
  - issue attention
  - Wikipedia pageviews
  - computational social science
  - UCDP
---

## Abstract

**Background.** Public attention is widely assumed to be a resource that can
constrain violence after a ceasefire is announced, yet the rate at which that
attention decays has not been measured for international peace processes. We
define the Peace Attention Half-Life (PAHL): the number of days for attention
to a conflict to fall to half of its post-announcement peak.

**Data and methods.** We combine daily Wikipedia pageviews across 14 language
editions with a curated table of [TK] verified ceasefires and related
agreements announced between 2015 and 2025, and with monthly conflict
fatalities from version 24.1 of the UCDP Georeferenced Event Dataset. Attention
is measured as log views in excess of an article-specific pre-announcement
baseline. We estimate PAHL event by event from the post-peak decay of that
excess attention, test it against a placebo distribution of pseudo-event dates,
and ask whether it is associated with the resumption of large-scale violence
within twelve months.

**Findings.** Median PAHL was [TK] days (interquartile range [TK] to [TK];
N = [TK] events). Attention decayed [TK] relative to placebo dates
(empirical p = [TK]). A longer half-life was associated with lower odds of
resumption (odds ratio [TK], 95% CI [TK] to [TK]; n = [TK]; cross-validated
AUC = [TK]). The War-Peace Attention Ratio [TK].

**Interpretation.** Attention to peace processes is short-lived and measurable,
and its decay rate is a candidate leading indicator for ceasefire durability.
Both the measurement and the association are exploratory: the event sample is
small, the design is observational, and no causal claim is made.

**Keywords:** ceasefires; attention; Wikipedia; peace duration; early warning;
multilingual measurement

## 1. Introduction

When a ceasefire is announced, the world looks. Cameras arrive, foreign
ministries issue statements, and the front pages of newspapers in a dozen
countries carry the same photograph of two delegations shaking hands. Then the
cameras leave. The question this paper asks is how fast they leave, whether the
speed differs across the languages in which people read about the war, and
whether the speed tells us anything about how long the peace will last.

That public attention matters to politics is not in dispute. The
issue-attention cycle (Downs 1972) describes how a problem emerges, commands
urgency, and fades; agenda-setting research shows that the salience media
assign to an issue shapes what publics and governments treat as important
(McCombs and Shaw 1972); and work on humanitarian intervention and foreign
policy argues that the intensity of news coverage changes the political cost of
inaction (Robinson 2002; Baum and Potter 2008; Gilboa 2005). Conflict itself
appears to respond to the attention cycle: Durante and Zhuravskaya (2018) find
that Israeli-Palestinian violence rises when the world is not watching. Yet
attention has never, so far as we are aware, been treated as a measurable
quantity in the study of peace processes themselves — something with a decay
constant, a distribution across conflicts, and a possible relationship to
outcomes.

This omission is odd, because the mechanism most often invoked to explain why
ceasefires fail is enforcement, and enforcement is expensive in attention.
Ceasefires without third-party monitoring or peacekeeping fail at much higher
rates than those with it (Fortna 2004; Hultman, Kathman and Shannon 2013), and
the durability literature explains that difference through verification,
guarantees, and the political costs that violations incur (Beardsley 2011;
Kreutz 2010; Walter 2002). Political costs require audiences. An agreement
whose violations are not being watched by anyone imposes very little cost on
the party that breaks it. If attention itself decays at a measurable rate, then
an agreement signed in a moment of global scrutiny faces a predictable
unwinding of that scrutiny, and the rate of unwinding should matter for whether
the agreement holds.

At the same time, the field of conflict forecasting has become quantitative and
mature on the violence side. Armed-conflict event datasets count and geolocate
fatalities at fine resolution (Sundberg and Melander 2013; Raleigh et al.
2010), and early-warning systems built on them produce monthly forecasts of
political violence across the world (Hegre et al. 2019). These systems consume
violence and structural covariates. They do not consume attention, except
occasionally as a control. There is therefore an asymmetry worth correcting:
we can measure how much people are killing, continuously and in near real time,
but not how much the world is watching.

Closing that gap requires three things that have only recently become jointly
available. The first is a high-frequency, cross-national, multilingual measure
of what people look at. Wikipedia is a defensible instrument for this purpose.
It is the largest reference work in human history, it publishes complete daily
view counts for every article in every language edition, and its usage tracks
public interest in observable ways (Moat et al. 2013; Yasseri, Sumi and Kertész
2012). Crucially for a study of international conflict, it is multilingual by
construction: the same event is described, and read about, in Arabic, Russian,
Ukrainian, Hebrew, Persian, Turkish, Chinese, Spanish, French, German,
Indonesian, Portuguese, Hindi, and English. A pageview series in Ukrainian for
the article on a ceasefire is not a poll, but it is evidence that people who
read Ukrainian are looking, on a given day, at that event.

The second is a verified event table. Ceasefires are announced constantly and
most of them are local, unverifiable, or never implemented. Measuring attention
decay requires anchoring the clock to dates that can be checked against wire
services, the United Nations, and the mediating parties themselves, and it
requires classifying what kind of instrument was announced, because a
humanitarian pause and a permanent peace agreement are not the same object of
attention.

The third is a violence measure with the right spatial and temporal resolution.
The Uppsala Conflict Data Program's Georeferenced Event Dataset provides
individual fatality events with country and dyad attribution (Sundberg and
Melander 2013), which allows us to ask, for each ceasefire, whether organised
violence in the same theatre returned to a substantial fraction of its
pre-agreement level within a year.

Bringing these three sources together, this paper makes four contributions.
First, it defines the Peace Attention Half-Life (PAHL): the number of days for
attention in excess of a pre-announcement baseline to fall to half of its
post-announcement peak. Second, it estimates PAHL for a curated set of
approximately forty ceasefires and related agreements announced between 2015 and
2025, across fourteen language editions, using an event-study design with a
robust exponential decay fit. This is, to our knowledge, the first
operationalisation of the issue-attention cycle for international peace
processes, and the first multilingual measurement of attention decay around
ceasefires. Third, it defines the War-Peace Attention Ratio (WPAR), the ratio of
attention to war concepts to attention to peace concepts in each language and
month, and estimates its level, trend, seasonal structure, and cross-language
dispersion over the 2015-2025 period. Fourth, it asks the question that gives
the measure its potential value: is a longer attention half-life associated with
a ceasefire surviving its first year? We test that association with logistic
and survival models, with explicit acknowledgement that the sample is small and
that the exercise is exploratory rather than confirmatory.

The paper is organised as follows. Section 2 situates the work in the
issue-attention, conflict-forecasting, and peace-durability literatures, and
states the gap precisely. Section 3 describes the three data sources and the
harmonisation required to join them. Section 4 sets out the measures and the
analysis plan, including the robustness checks and the conditions under which
the central claims would fail. Section 5 reports results. Section 6 discusses
what the results do and do not imply. Section 7 states limitations, and Section
8 concludes.

## 2. Background and Related Work

### 2.1 The issue-attention cycle and its measurement

The idea that public attention to a problem follows a characteristic curve is
old. Downs (1972) argued that social problems pass through a sequence in which
they are discovered, met with alarm, met with realisation of cost, and then
gradually displaced from public view, and that the displacement is a structural
feature of democratic attention rather than a failure of the public. The
mechanism is competitive crowding: attention is finite, and each newly urgent
problem bids attention away from the last. Simon (1971) had already stated the
underlying economics, and the resulting literature on the attention economy
(Davenport and Beck 2001) treats attention as a scarce allocable resource rather
than a free by-product of information supply.

Agenda-setting research gave the cyclical argument an empirical footing by
demonstrating that the salience media attach to issues is transmitted to
publics (McCombs and Shaw 1972; Brossard, Shanahan and McComas 2004). The
foreign-policy variant concerns us most: Baum and Potter (2008) review evidence
that media coverage conditions public support for intervention, and the "CNN
effect" literature debates whether coverage drives or merely accompanies
decisions to intervene (Robinson 2002; Gilboa 2005). Two findings from that
tradition are directly relevant. Coverage of distant conflicts is uneven and
strongly event-driven, and downturn in coverage after a peak is typically fast.
What is missing from this literature is a standard unit: no one reports that
attention to a given crisis falls by a factor of two every k days, largely
because the available measures of attention (survey salience, front-page counts,
minutes of airtime) are inconvenient to run continuously for many crises at
once.

Two literatures supply candidate units. Work on the decay of online information
shows that news attention and content popularity follow heavy-tailed decay
curves, with the "half-life" of a news item used informally to describe how
quickly it leaves circulation (Leskovec, Backstrom and Kleinberg 2009; Szabo and
Huberman 2010). This work establishes that decay curves are estimable from
digital traces, but it is about items and memes — a link, a story — not about
sustained political processes whose salience is itself an object of contestation.
Epidemiological and nowcasting applications of search and view data (Choi and
Varian 2012) show that digital traces can serve as high-frequency indicators of
latent public states. Neither strand has been applied to peace processes.

### 2.2 Violence-side forecasting

The quantitative study of conflict has concentrated its measurement effort on
violence. The UCDP Georeferenced Event Dataset records individual violent events
with dates, locations, actors, and fatality estimates (Sundberg and Melander
2013), and the ACLED project provides a comparable real-time event stream
(Raleigh et al. 2010). Forecasters use these data to predict the onset,
escalation, and termination of conflict. The ViEWS system (Hegre et al. 2019)
produces monthly forecasts of political violence at subnational resolution for
Africa and the Middle East; other systems add structural covariates, climate
indicators, or network features. The epistemic gain from this programme is real:
we now know a great deal about when and where violence is likely to rise.

Forecasting systems are almost entirely supply-side, in the sense that they
model the capacity and incentives of armed actors. Where publics appear in
these models, they appear as a control or as a channel, not as a measured
quantity of interest. This is a defensible choice for violence prediction: the
violence-generating process is largely internal to armed actors. It is a much
weaker choice for understanding why some ceasefires survive and others do not,
because the enforcement of a ceasefire runs partly through audiences.

### 2.3 Peace durability and the enforcement gap

The study of ceasefire and peace-agreement durability has identified a robust
set of predictors. Agreements that are verified by third parties, that
institutionalise monitoring, and that include peacekeeping deployments are more
likely to hold (Fortna 2004; Hultman, Kathman and Shannon 2013). Mediated
agreements face a distinct commitment problem, and the durability of mediation
outcomes depends on the guarantors' continued engagement (Beardsley 2011).
Power-sharing provisions and integration arrangements shape the hazard of
renewed war (Walter 2002; Hartzell and Hoddie 2007). Kreutz (2010) shows, using
the UCDP Conflict Termination dataset, that how a conflict ends — through
victory, negotiated settlement, or ceasefire — strongly conditions whether it
restarts.

Recent work has begun to treat ceasefires as an object with their own logic
rather than merely a stage in a settlement process (Clayton and Sticher 2021),
and to document the enormous heterogeneity of ceasefire instruments and of what
they are supposed to accomplish. This literature has two relevant gaps. First,
its outcome variables are violence-side and structural: agreement provisions,
guarantors, troop deployments, battlefield balances. The enforcement mechanism
that runs through public scrutiny is hypothesised but not measured. Second,
attention is treated as constant: no durability model, to our knowledge,
includes a measured rate at which public interest in the agreement declines,
because no such measure has existed.

If attention is an enforcement resource, its decay should enter the durability
literature in the same way that the decay of an army or of a guarantor's
commitment does. That is a falsifiable proposition, and it motivates the design
below.

### 2.4 Wikipedia as a multilingual attention instrument

Wikipedia pageviews have a short but productive history as a behavioural
indicator. Moat et al. (2013) find that views of financial articles contain
information about subsequent market movements; Yasseri, Sumi and Kertész (2012)
document strong circadian and weekly structure in editorial activity, which
implies that view series must be treated with explicit attention to cyclic
artefacts; and a large methodological literature establishes that view counts
are stable enough for time-series work when bot traffic is filtered and
seasonality is handled. Compared with surveys, pageviews have the advantages of
being continuous, free, complete, and population-scale; compared with social
media, they have the advantage of not requiring a platform API or a panel of
consenting users, and of being available for readers rather than only for
posters.

The multilingual character of Wikipedia is the property that makes this study
possible. Language editions are partially independent, with their own editing
communities, their own biases, and their own readerships (Hale 2014), and
article titles are programmatically linked across editions through the
MediaWiki langlinks system. A ceasefire in Gaza is read about in Arabic, Hebrew,
and English; a ceasefire in eastern Ukraine is read about in Ukrainian, Russian,
and English. Using langlinks rather than hand translation makes the
multilingual construction auditable and reproducible, and it allows us to ask
whether the speed of looking away differs across the audiences for whom the
conflict is local and those for whom it is distant.

Wikipedia pageviews are not public opinion. They over-represent literate,
online, and young populations; they include incidental and automated traffic;
and they measure engagement with a topic, not support for a policy. These
limitations are serious and are returned to in Section 7. They do not, however,
invalidate the instrument for the descriptive question of whether, and how fast,
attention to a named event fades, which is the question we primarily ask.

### 2.5 The gap

Our reading of these literatures identifies four points at which this paper
departs from prior work. No existing study has defined a half-life for
attention to peace processes, so the quantity we estimate is new. No existing
study has estimated attention decay across many language editions
simultaneously, so the cross-linguistic comparison of decay rates is new. No
existing study has joined attention time series to a verified ceasefire table,
so the event study of attention around peace announcements is new. And no
existing study has tested whether the rate of attention decay carries
information about ceasefire survival, so the predictive association is new.
Each of these claims is a claim about the absence of prior work, and Section 2
should be read with that caveat: absence of evidence in our reading is not
proof, and the search was conducted in 2026 against the literature available at
that time.

The framework also generates clear falsification conditions, stated in Section
4.8: if attention decay around ceasefire announcements is indistinguishable from
decay around placebo dates, the measure does not capture event-specific
attention; if the measured half-life shows no association with resumption after
permutation testing, the predictive claim does not survive; and if attention to
peace concepts decays more slowly than attention to war concepts, the
"attention deficit" framing that motivates the WPAR is wrong and must be
reversed. We report all three outcomes whichever way they fall.

## 3. Data

### 3.1 Attention: Wikimedia pageviews

Attention is measured with daily pageview counts from the Wikimedia Analytics
Query Service, which publishes, for every article in every language edition, the
number of requests classified as user traffic (desktop and mobile, excluding
automated agents) at daily granularity from 1 July 2015 onward. For each
language and each article we retrieve the complete daily series for the period
1 July 2015 to 1 November 2025, so that every event in the sample has a
pre-announcement baseline of at least several months and, for events near the
end of the period, a shorter but usable follow-up. Requests are made per
article and cached to disk, with retry and backoff on rate limiting, so the
retrieval is resumable and the resulting series are identical on re-run.

Article selection proceeds in two concept families and one event-based set. The
war family consists of ten English Wikipedia articles denoting armed conflict and
its instruments: War, Armed conflict, Civil war, Invasion, Airstrike, Genocide,
Terrorism, Military occupation, Refugee, and War crime. The peace family
consists of eleven articles denoting the institutions and practices of
peacemaking: Peace, Ceasefire, Peace treaty, Peacebuilding, Mediation,
Diplomacy, Reconciliation, Disarmament, Demobilization, Peacekeeping, and
Humanitarian aid. These two families are used for the War-Peace Attention Ratio
in Section 4.4 and, separately, for a family-level comparison of decay rates.
The event-based set consists of [TK] conflict-specific articles, one or more per
event in the ceasefire table, resolved from the English article for the relevant
war; these support the event-level PAHL estimates in Section 4.3.

For each English seed article we resolve the corresponding title in each of
fourteen target language editions - Arabic, Chinese, English, Persian, French,
German, Hebrew, Hindi, Indonesian, Portuguese, Russian, Spanish, Turkish, and
Ukrainian - through the MediaWiki langlinks API rather than by hand translation.
The fourteen languages span the theatres of the conflicts in the sample (Arabic,
Hebrew, Russian, Ukrainian, Persian, Turkish) and the principal mediator and
donor-language publics (English, French, German, Spanish, Portuguese, Chinese,
Indonesian, Hindi). Where no langlink exists, the article is treated as not
existing in that edition and no series is created; such absences are structural
(they reflect editorial coverage, not zero readership) and are not coded as zero
attention. Titles are normalised and URL-encoded before requests. The resulting
panel is unbalanced by construction, which is appropriate: a language edition
that has never written an article about a war is a finding about coverage, not a
missing value to be imputed.

### 3.2 Ceasefires: a curated and verified event table

We curate a table of ceasefire, truce, cessation-of-hostilities,
de-escalation, and peace-agreement events announced between 2015 and 2025. An
event is included if it (i) was announced for a civil war, interstate conflict,
or sustained non-international armed conflict with an identifiable theatre
country; (ii) applied to the conflict as a whole or to a substantial geographic
component of it, rather than to a single local encounter; (iii) received
regional or global news coverage, so that there is a plausible cross-language
attention response; and (iv) can be dated to a day by at least one authoritative
source that states the date explicitly.

Events are excluded if the announcement was never implemented and no
implementing date can be identified, if the instrument was a purely tactical
humanitarian pause with no public announcement beyond a local agreement, or if
the date cannot be verified against an independent source. Where announcement
and entry-into-force dates differ materially, we use the announcement or
entry-into-force date of the public statement, because that is the moment at
which attention is expected to react; the choice is recorded for every event.

Each record carries a stable identifier, the date, the theatre country (ISO3),
the conflict name, the participating actors, an instrument type drawn from five
categories (ceasefire, humanitarian pause, peace agreement, truce, and
de-escalation), an expected-salience label, at least one source URL, and a
verification flag that is set only after the date has been checked against the
source text. The verification discipline matters more than it might appear:
several of the most widely cited ceasefires in this period have dates that
differ across reporting conventions by days or weeks, and misaligning the clock
would corrupt every downstream estimate.

### 3.3 Violence: UCDP Georeferenced Event Dataset

Outcomes are measured with version 24.1 of the Uppsala Conflict Data Program
Georeferenced Event Dataset, which records individual organised-violence events
with date, location, actors, and a best fatality estimate (Sundberg and Melander
2013). We aggregate events to monthly total fatalities by country (for the
theatre-level resumption definition) and by conflict dyad (for a
conflict-specific alternative). The extraction covers 2014 through 2025, one
year longer at the start than the event table, so that every event in the sample
has a pre-announcement baseline of at least six months even if announced in
early 2015. As with any event-based fatality data, the series reflects
reporting coverage as well as violence; we use it as a relative rather than
absolute measure and define outcomes in terms of ratios to a local pre-event
baseline rather than absolute counts.

### 3.4 Harmonisation

Joining the three sources requires three mappings: from ceasefire event to
theatre country ISO3 code; from theatre country to the monthly UCDP series; and
from event to the set of article series whose attention is expected to respond.
The first is straightforward for events with a single theatre and is recorded
explicitly for the small number of multi-theatre events. The second is direct
for country-level series. The third is the only one requiring judgement: an
event is matched to the conflict-level article for its war where one exists, and
to regional coverage where the conflict has no dedicated article in a given
language. We record the matching explicitly so that every PAHL estimate can be
traced to a specific article and language.

Time is handled in the natural time zone of the event for the alignment of the
announcement to a calendar day, and all decay windows are defined in elapsed
days from the event date. Missing pageview days inside an article's existence
period are filled with zeros, which is correct for a series that counts
requests; days before an article's creation are not filled, because a
zero would misrepresent non-existence as inattention.

### 3.5 Sample description

Table 1 summarises the three sources. The final analytic sample contains [TK]
ceasefire events covering [TK] theatre countries, of which [TK] are classified as
ceasefires, [TK] as peace agreements, [TK] as humanitarian pauses, [TK] as
truces, and [TK] as de-escalation arrangements. The pageview panel contains
[TK] article-language series and [TK] daily observations, with an average of
[TK] language editions available per event article.

Table 1. Data sources and analytic sample.

| Source | Unit of observation | Resolution | Coverage in this study | Volume |
|---|---|---|---|---|
| Wikimedia pageviews | article x language x day | daily | 2015-07-01 to 2025-11-01 | [TK] series; [TK] observations |
| Curated ceasefire table | event | event | 2015-2025 | N = [TK] events |
| UCDP GED v24.1 | fatality event, aggregated | event to month | 2014-2025 | [TK] events aggregated |

### 3.6 Licensing, ethics, and provenance

All three sources are public. Wikimedia pageview data are published under
Wikimedia's open data policy and the underlying encyclopaedia text under CC BY-SA;
the study uses only aggregate request counts and no individual-level data. UCDP
data are distributed for research use with citation; we cite the dataset and its
version in the data availability statement. The curated ceasefire table is
released with this paper under CC BY 4.0, with every row traceable to a URL.
No human subjects are involved, no personal data are processed, and no
information is used that is not already public. Retrieval dates, API endpoints,
and file hashes are recorded in the repository so that the frozen dataset can be
reconstructed.

## 4. Methods

### 4.1 Measures

For article a in language l on day t, let V(a,l,t) be the number of user
pageviews. Attention is defined on the log scale, A = log(1 + V), because view
distributions are strongly right-skewed and because a constant proportional
decline is the natural object for a half-life. The baseline for article a
around an event at date t0 is a 28-day centred moving average of A computed on a
series in which the +/-14 day window around t0 is masked, so that no attention
generated by the announcement itself can enter the reference level. The masking
window is deliberately wider than the announcement response is expected to be,
so that the baseline represents pre-announcement attention even if the response
begins early through anticipation or leaks.

Excess attention is then E = A - baseline. Because A is a log and the baseline
is a mean of logs, E is approximately the log ratio of views to the reference
level: E = 0 means attention at its pre-announcement level, E = log(2)
corresponds to a doubling, and so on. Excess attention is the quantity plotted,
aggregated, and fitted throughout. It has the useful property that events of
very different magnitude are put on a comparable multiplicative scale, which
matters when pooling a local truce and a globally covered agreement.

### 4.2 Event-study design

Each ceasefire is aligned at t = 0 on its verified announcement date. For each
event and each matched article series we compute excess attention for t in
[-90, +365], a window long enough before the event to characterise the
pre-announcement level and long enough after it to observe a full decay for all
but the very slowest cases. Series are included for an event if the article
existed (langlink present) at t = 0. Days outside an article's existence are
excluded rather than zero-filled.

The primary event-study object is the mean excess attention by day from t = 0,
computed across all event-series pairs, with two important caveats that shape
the interpretation. Because events differ enormously in salience, the pooled
mean is dominated by the largest events; we therefore report both the pooled
curve and event-level curves, and never interpret the pooled peak as
representative of a typical ceasefire. And because attention before t = 0 is not
zero, the pooled curve includes a pre-period that can reveal anticipation and
pre-existing trends, which we inspect rather than assume away.

The peak of the response is located per event as the day of maximum excess
attention within [-7, +30], a window chosen to allow both immediate and slightly
delayed announcement responses while excluding later violence-driven spikes
that are not responses to the announcement itself. Events for which no day in
that window has positive excess attention are recorded as having no detected
response and are reported, not silently dropped.

### 4.3 Peace Attention Half-Life

PAHL is defined as the number of days for excess attention to fall to half of
its post-announcement peak. Operationally, for each event-series pair with a
detected peak we fit the model

    E(t) = A exp(-lambda (t - t_peak)) + c

on the post-peak window from t_peak to t_peak + H days, where H is a common
horizon and c allows for a residual post-decay offset. Because E is already a
log quantity, the multiplicative decay model is linear in log excess attention
minus the offset, and we estimate lambda by robust (Huber) weighted regression of
log-excess on elapsed days since peak, with Theil-Sen as a check on the slope.
The half-life follows as PAHL = ln(2) / lambda. The fit is restricted to days on
which excess attention is positive, because a log of a non-positive quantity is
undefined; this conditions the estimate on the post-peak decay being a decay,
which is the object of interest but also a selection that we report explicitly.

Event-level PAHL values are summarised by median and interquartile range across
events rather than by a mean, because the reciprocal relation between lambda and
half-life makes the distribution right-skewed and because a few slow decays would
otherwise dominate. Uncertainty in the summary is characterised by a
nonparametric bootstrap over events (1000 resamples of events with replacement,
median recomputed in each) and by a residual bootstrap for per-event slopes.
Estimates are produced separately for the pooled sample, for the war-adjacent
and peace-adjacent article families, and for each language with sufficient
series, which is the analysis that makes the "does the audience closest to the
war look away slower" question answerable.

### 4.4 War-Peace Attention Ratio

WPAR is defined monthly and per language as the ratio of total attention to the
war family to total attention to the peace family:

    WPAR(l,m) = sum over war articles of V / sum over peace articles of V

computed on raw views, so that it has a direct interpretation as "how many
reads the war concepts receive for every read of the peace concepts". The ratio
is a level measure whose absolute value depends on the number and popularity of
articles in each family; we therefore interpret differences over time within a
language and differences in trend across languages, and we never interpret the
absolute level as a measure of public sentiment. Trend is estimated by OLS of
WPAR on a monthly time index with Newey-West HAC standard errors, and
seasonality is characterised with month-of-year effects and with a
locally-estimated seasonal decomposition for visual inspection. Cross-language
dispersion is summarised monthly by the coefficient of variation across
languages, and the languages with the highest and lowest mean WPAR over the
period are reported, with the caveat that family composition is not perfectly
comparable across editions because article sets differ.

### 4.5 Outcome coding: resumption of violence

A ceasefire is coded as having resumed if, within twelve months after the event
date, monthly fatalities in the theatre country exceed 25 per cent of the mean
of the six months preceding the event for at least two consecutive months. The
ratio-based definition is deliberate: absolute fatality thresholds would
classify every ceasefire in a high-intensity war as failed and every ceasefire in
a low-intensity conflict as successful. Requiring two consecutive months
prevents a single atrocity or data artefact from driving the outcome. The
primary analysis uses the country-level series; a dyad-level variant is reported
as a robustness check. Time to resumption is measured in months from the event
date to the first month of the qualifying pair, censored at twelve months for
ceasefires that hold. Thresholds of 10 and 50 per cent, and a variant requiring
three consecutive months, are reported in Section 4.7. We report the base rate of
resumption in the sample before any modelling, because with a small sample the
base rate is more informative than any coefficient.

### 4.6 Predictive models

The predictive question is whether PAHL carries information about resumption
beyond what is already known at the time of the announcement. We estimate a
logistic regression of resumption on standardised PAHL, log baseline fatalities
(the log of the six-month pre-event mean, which captures how much violence was
being suspended), instrument type, and region. Coefficients are reported as
odds ratios with 95 per cent confidence intervals, together with the sample size
and the number of events in each outcome category. Discrimination is assessed by
cross-validated area under the ROC curve, using stratified folds appropriate to
the small sample, and we report the in-sample AUC only alongside the
cross-validated one so that the difference between fitting and predicting is
visible.

Because resumption is a timing process as well as a binary outcome, we also
estimate a Cox proportional-hazards model for time to resumption with the same
covariates, report hazard ratios, and check the proportional-hazards assumption.
All inference here is explicitly exploratory. With roughly forty events and two
outcome classes, the models are underpowered by any conventional standard, the
confidence intervals will be wide, and a coefficient that fails to reach
significance is not evidence of absence. We therefore report effect sizes and
intervals as the primary quantity and treat p-values as descriptive.

### 4.7 Robustness and specification checks

Six families of checks are pre-specified and reported regardless of outcome.
First, placebo events: for each ceasefire we draw 500 pseudo-event dates
uniformly from the same calendar year and recompute the full pipeline - baseline,
peak detection, decay fit - at each pseudo-date, producing a placebo
distribution of PAHL. The observed half-life is compared with this distribution
to obtain an empirical p-value, which asks whether the measured decay around
real announcements is distinguishable from decay around arbitrary dates in the
same period. This is the single most important check in the paper: if attention
around ceasefires decays no differently from attention around random days, the
event-specific interpretation fails.

Second, alternative decay windows: fits ending at +30, +90, and +270 days after
the peak, to test whether the half-life is an artefact of the fitting horizon.
Third, alternative resumption thresholds at 10 and 50 per cent of the pre-event
mean and a three-consecutive-month variant. Fourth, leave-one-out: the PAHL
median and the cross-validated AUC are recomputed with each event omitted in
turn, to identify whether a single ceasefire drives the results. Fifth, a
permutation test: the PAHL-resumption association is recomputed under 1000
random permutations of PAHL across events, giving a null distribution for the
association statistic. Sixth, a language-subset sensitivity analysis: estimates
restricted to English-language series are compared with estimates using all
fourteen editions, which separates a global-attention result from one carried by
the largest edition.

### 4.8 Falsification conditions

The design specifies three outcomes that would count against the framework, and
we commit to reporting them in full. If the observed PAHL distribution is
indistinguishable from the placebo distribution, then attention decay around
ceasefires is not event-specific and PAHL should not be interpreted as a
measure of response to the announcement. If the association between PAHL and
resumption vanishes under permutation, then no predictive claim survives and
the paper reports a null. If attention to the peace family decays more slowly
than attention to the war family, then the attention-deficit framing that
motivates WPAR is wrong, and the correct reading is that peace concepts have
longer-lived salience than the framework assumed. Each of these is a possible
result, and each is reported in Section 5 whichever way it falls.

### 4.9 Reproducibility

The pipeline is a single Python codebase with a one-command reproduction path.
Retrieval is cached and resumable, so a re-run reconstructs the frozen datasets
from the recorded endpoints without depending on live API availability; the
analysis and figure stages regenerate every number and every figure from the
cached data with fixed random seeds. Versions of the data sources, the retrieval
date, and the analysis code are recorded in the repository, and a separate
verification script checks that each numeric claim in the manuscript matches the
machine-readable results file. Code is MIT-licensed and data and manuscript are
released under CC BY 4.0, so that the measurement can be criticised, extended,
or re-estimated with different thresholds.

### 4.10 Interpretational stance

Nothing in this design identifies a causal effect. Attention and violence are
jointly determined: a ceasefire that is visibly collapsing generates both
attention and fatalities, and a conflict that is boring generates neither. The
estimates in this paper are descriptive (how fast does attention decay, and how
does that differ across events and languages) and predictive (does the decay
rate carry information about resumption). Where we use the language of
association, we mean association. Where the results are consistent with an
enforcement mechanism, we say so and we say that alternative mechanisms are
equally consistent. The purpose of the exercise is to establish that the
quantity can be measured and to show what its measurement implies, not to
establish that attention causes peace to hold.
