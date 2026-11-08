# Related Work and Novelty Assessment
### "The Half-Life of Peace": attention decay to ceasefires across Wikipedia language editions

*Literature review prepared by the project's literature scout. Every citation in Section 6 was checked against Crossref/OpenAlex records (title, authors, year, venue, DOI) and every URL in this file was resolved during preparation. Claims attributed to prior work are based on the published abstract or full text of the cited item. Items that could not be verified are listed in the Appendix rather than cited. Negative search results are reported with the query terms used, in Section 4.3.*

---

## 1. The attention literature

### 1.1 The issue-attention cycle and punctuated attention

The intellectual ancestor of our project is Anthony Downs' "issue-attention cycle" (Downs, 1972). Downs argued — on the basis of observation of US domestic (especially environmental) policy — that public attention to a problem follows a characteristic sequence: the problem "suddenly leaps into prominence, remains there for a short time, and then — though still largely unresolved — gradually fades from the center of public attention." Two features of Downs' formulation are directly relevant to us. First, the cycle is explicitly about *the attention paid to a problem*, not about the problem's severity; the fade is driven by boredom, rising costs of further action, and displacement by new issues. Second, Downs' evidence was impressionistic: he offered a stage model, not a rate parameter.

The agenda-setting tradition grounded the first half of this claim empirically. McCombs and Shaw (1972) established that the salience of issues in mass media transfers to the salience of issues in the public mind, and Galtung and Ruge (1965) had already specified the selection rules ("news values") that make some events reportable at all. Baumgartner and Jones (1993) and Jones and Baumgartner (2005) re-cast the cycle in terms of punctuated equilibrium: attention is not smoothly reallocated but lurches between long periods of neglect and short bursts of high salience, because information processing is boundedly rational and issues compete for a fixed capacity. This literature is the source of the *shape* of our dependent variable but provides no estimate of its *rate*: it is a theory of why decay happens, not a measurement of how fast.

**Implication for us.** Downs gives us the vocabulary and the qualitative prediction; he does not give us a half-life. Our PAHL metric is a parameterisation of a 50-year-old verbal theory, and we should say so plainly rather than claim to have discovered attention decay.

### 1.2 Attention decay and memory half-lives

A separate, largely quantitative literature has actually estimated decay rates, mostly on cultural and scientific rather than conflict data.

- **Candia et al. (2019)** is the single most important methodological precedent. Using Wikipedia page views, Google Trends, and citation records, they find a *universal bi-exponential* decay of collective attention: a fast "communicative" component with a half-life of days, followed by a much slower "cultural" component with a half-life of years, with the weight shifting toward the slow component as an item ages. Their key theoretical move — separating a short-lived communicative memory from a durable cultural memory — maps closely onto what we expect for ceasefires: a spike at announcement, a rapid fade, and a residual "frozen conflict / peace process" baseline.
- **Lorenz-Spreen et al. (2019)** show that this decay is *accelerating* across decades and domains: topics now receive shorter intervals of collective attention, consistent with a model of competition for finite attention under rising content production.
- **Parolo et al. (2015)** estimate "attention decay in science": citations to papers decline roughly exponentially, and the decay constant differs systematically across fields — direct evidence that a half-life is a meaningful, estimable, and field-varying parameter.
- **Wu and Huberman (2007)** and **Yang and Leskovec (2011)** provide the canonical early results on novelty-driven attention spikes and on the characteristic temporal shapes (spikes, news cycles, "rising" patterns) of online media; **Lehmann et al. (2012)** classify collective attention trajectories into distinct dynamical classes.
- **Pfeffer and Matter (2023)** estimate a literal "half-life of a tweet", i.e. the time for engagement to fall to half its peak, and show the estimate is sensitive to the operational definition of half-life.
- **Roediger and Abel (2015)** connect this computational work to the cognitive-science tradition of Ebbinghaus-style forgetting curves, which is where the term "half-life" of memory originates.

**Implication for us.** The *measurement machinery* for PAHL is not new: bi-exponential fits, half-life estimation, and the distinction between short and long memory all exist. What does not exist is an application to *ceasefire announcements* as events, or a test of whether the resulting rate has *predictive value for political outcomes*. That is the gap we occupy, and we should frame PAHL as a transfer of an established estimator to a new event class, not as a new estimator.

### 1.3 Media, foreign policy, and the CNN effect

The "CNN effect" literature asks whether media coverage drives foreign policy. Livingston and Eachus (1995) studied Somalia and concluded that the effect is conditional — coverage mattered for *when* and *how* policy responded, not for whether it responded — and they explicitly distinguished "CNN effects" from "CNN-induced" policy. Robinson (1999) supplied the most influential synthesis, arguing the effect is strongest where policy is uncertain; Gilboa (2005) reviewed the field and concluded that the evidence supports only a conditional, agenda-setting version of the thesis. Baum and Potter (2008) integrated the mass-media, public-opinion, and foreign-policy literatures into a single framework.

Two findings in this tradition matter for our design.

First, **selectivity is the norm, and neglect has consequences**. Hawkins (2011) documents the "other side of the CNN effect": most of the world's conflicts go largely unreported, the deadliest are among the most ignored, and the consequence of ignoring conflict is unchecked death tolls because neither policy response nor humanitarian aid is forthcoming. Kogen and Price (2011) show that the Livingstonian framework can be tested with polling data and that public opinion does not straightforwardly track coverage. Kinnick et al. (1996) and Moeller (1999) name the underlying mechanism — *compassion fatigue* — whereby repeated exposure to distant suffering produces audience burnout and declining coverage.

Second, **attention is causally consequential, not merely descriptive**. Eisensee and Strömberg (2007) provide the cleanest identification in this literature: US disaster relief depends on whether a disaster happens to coincide with other newsworthy events (e.g. the Olympic Games), implying that relief is driven by news coverage and that unrelated news *crowds out* coverage of need. This is the strongest existing evidence that attention is a real allocative variable rather than an epiphenomenon, and it is the template for the causal argument we want to make about ceasefires.

**Implication for us.** The CNN-effect tradition establishes (a) that attention to conflict is selective and decays, and (b) that attention has allocative consequences. It does not treat attention itself as a *time series with an estimable decay rate*, nor does it use attention decay to forecast the collapse of a specific agreement.

### 1.4 Rally-round-the-flag and conflict salience

The rally literature is the closest work on *aggregate public response to conflict events*. Mueller (1970) established the rally phenomenon in presidential approval data; Baum (2002) disaggregated it by party and political sophistication and showed that different audiences respond differently to uses of force, over all major US uses of force 1953–1998.

**Implication for us — and an important boundary.** The rally literature measures *individual-level opinion* (approval, support) at monthly or event-level resolution, typically in a single country, and it is about *onset*, not decay. It offers no cross-national, cross-lingual measure, no half-life, and no link to whether an agreement survives. Our WPAR and PAHL metrics are aggregate-attention measures, not opinion measures, and we must be careful not to claim to be measuring "support for peace".

---

## 2. The peace durability literature

### 2.1 Ceasefires as an object of study

Ceasefires have only recently become a research object in their own right, rather than a footnote to peace agreements. The field-defining interventions are:

- **Bara, Clayton and Rustad (2021)**, the introduction to a special issue, note that ceasefires are a ubiquitous feature of violent conflict — more than 2,000 between 1989 and 2020 — and that they are theoretically under-specified: they can be tactical, humanitarian, or pre-negotiation devices.
- **Clayton, Nathan and Wiehler (2021)** argue that "ceasefire success" is under-conceptualised and should be assessed on two inter-related dimensions (broadly: whether violence stops, and whether the ceasefire advances the peace process). This is directly relevant because it tells us that "ceasefire collapse" is itself a contested outcome variable, not a natural kind.
- **Clayton and Sticher (2021)** provide the theoretical core: different bargaining problems generate three logics of ceasefire design, and the effect of a ceasefire depends on both the logic and the provisions. Empirically they model *ceasefire survival* using PA-X provisions and **UCDP georeferenced event data, with conflict deaths as the main measure of whether a ceasefire remains in place**.
- **Sticher (2022)** reviews why ceasefire violations occur and how they relate to strategic decision-making; almost all ceasefires experience violations, which means our outcome must be defined in terms of *intensity thresholds* rather than any violation.
- **Åkebo (2016)** provides the comparative case-study treatment of ceasefire agreements within peace processes.
- **Karakuş and Svensson (2017)** and **Lundgren, Svensson and Karakuş (2023)** are the closest quantitative work on ceasefire effects on violence. The latter analyses 145 local ceasefire agreements in Syria (2011–2019) with interrupted time-series and spatial panel models on georeferenced violence data, and finds that local ceasefires can trigger either escalation or de-escalation; de-escalation is more likely in the long term where signatories share a history of interaction.
- **Clayton, Nygård, Rustad and Strand (2022)** introduce the ETH/PRIO Civil Conflict CeaseFire (CF) dataset: 2,202 ceasefires across 66 countries and 109 civil conflicts, 1989–2020, coded for actors, class, purpose, coverage and end date. **This is the natural sampling frame for our curated table of 35–45 agreements**, and we should either use it or justify departing from it.
- The **PA-X Peace Agreement Database** (Bell et al., 2019) supplies the coded text of agreements and ceasefire provisions.

### 2.2 Peace-agreement and post-conflict durability

The broader durability literature supplies our outcome side and our control variables:

- **Fortna (2004, 2008)** shows that peacekeeping after civil wars substantially lengthens the duration of peace, while explicitly addressing the non-random deployment of peacekeepers.
- **Walter (2002)** explains settlement and durability in terms of credible commitment: settlements fail when belligerents cannot commit not to exploit the other's demobilisation.
- **Hartzell, Hoddie and Rothchild (2001)** and **Hartzell and Hoddie (2003)** show that institutionalised power-sharing — territorial, military, political, economic — is associated with more durable peace.
- **Beardsley (2011)** argues that mediation buys agreements at the price of durability: mediated settlements are less stable because they reduce the belligerents' own ownership of the terms. This is a direct precedent for the structure of our hypothesis — a feature of the *settlement environment* predicts collapse — and it is the single most important theoretical rival we must control for.
- **Kreutz (2010)** introduces the UCDP Conflict Termination dataset, disaggregating conflicts into episodes with start/end dates and means of termination; this is the canonical treatment of "how conflicts end" and the source of the dyadic/episodic logic we borrow.
- **Hultman (2010)** and **Hultman, Kathman and Shannon (2013)** study whether peace operations reduce or spur violence against civilians, the latter finding that larger deployments of military and police personnel reduce civilian targeting (monthly data on UN personnel, 1991–2008).

**Implication for us.** This literature is rich in *structural* predictors of durability — institutional design, third-party guarantees, power-sharing, mediation, troop levels — and it is uniformly measured on the violence/agreement side. **In none of these works is public attention a variable, let alone a predictor.** The dependent variable (violence resumption) is well-established and we should adopt standard operationalisations from it (UCDP GED-based intensity thresholds; see Section 4.4).

### 2.3 Conflict forecasting and early warning

- **Hegre et al. (2019)** present ViEWS, a transparent, publicly available political-violence early-warning system producing monthly country- and sub-national forecasts up to 36 months ahead for state-based conflict, non-state conflict and one-sided violence in Africa.
- **Ward, Greenhill and Bakke (2010)** make the methodological case that conflict studies optimise for statistical significance rather than predictive performance, and that this has produced little genuine forecasting capacity.
- **Chadefaux (2014)** shows that the *tone and volume of news reporting* carries early-warning signal for war — the closest existing precedent for using media-derived text as a leading indicator of political violence.
- **Mueller and Rauh (2018)** predict political violence from newspaper text with a transparent, replicable pipeline, and is the strongest precedent for treating a media/attention corpus as a predictor of conflict.

**Implication for us.** Forecasting is an established frame and we should adopt its evaluation conventions (out-of-sample prediction, proper scoring rules, no leakage) rather than presenting a correlational result. But the forecasting literature predicts *onset or intensity of violence from structural or textual covariates*; it does not predict *the collapse of a ceasefire from the decay rate of attention to it*.

---

## 3. Wikipedia pageviews as a data source

Wikipedia pageview data are an established social-science sensor, and the relevant canon is well defined.

**Foundational descriptive work.** Spoerri (2007) was among the first to analyse what is popular on Wikipedia and why, establishing that page-view distributions are extremely skewed and event-driven. Yasseri et al. (2012) use Wikipedia to study conflict and coordination in collaborative editing.

**Page views as a proxy for offline behaviour.** Moat et al. (2013) show that Wikipedia usage patterns carry information about forthcoming stock-market moves; McIver and Brownstein (2014) show that Wikipedia usage estimates influenza-like-illness prevalence in near real time; Tizzoni et al. (2020) show that news exposure shapes collective attention during an epidemic. Yasseri and Bright (2016) provide the most careful methodological treatment of page views as a measure of public attention for electoral prediction, and are explicit about the assumptions required — a paper we should cite and imitate in our measurement section.

**Attention dynamics and collective memory.** García-Gavilanes, Tsvetkova and Yasseri (2016) study the dynamics and biases of online attention using aircraft crashes, showing how event characteristics shape the attention trajectory. García-Gavilanes, Mollgaard, Tsvetkova and Yasseri (2017) use Wikipedia page views to show that collective memory of past events decays but is reactivated by commemoration — the clearest demonstration that Wikipedia captures *memory*, not just curiosity. Candia et al. (2019), discussed above, relies on page views as a primary source.

**Attention inequality and cross-lingual structure.** Ruprechter et al. (2023) analyse 17,490 event articles across four Wikipedia language editions and show that attention and coverage are skewed toward events in economically developed countries, and that severity (e.g. deaths in a disaster) matters too — a direct caution that page views measure *attention*, which is not the same as *importance*, and a paper we must engage because it is the closest existing cross-lingual analysis of Wikipedia event attention. Gildersleve and Lambiotte (2023) develop temporal community detection to identify networked topics of collective attention on Wikipedia and to examine how current events are integrated into the encyclopaedic topical structure — methodologically the closest work to our article-set construction.

**Implication for us.** The data source is legitimate and has a canon. But the existing applications are elections, markets, disease, disasters, cultural memory, and general event attention. **We found no study that uses Wikipedia page views to measure attention to armed conflict or to ceasefires.** That is a genuinely open application, not a contested one.

---

## 4. Prior work on attention + ceasefires specifically

This section is the load-bearing part of the novelty claim, so it separates what exists from what does not.

### 4.1 What DOES exist

1. **Qualitative and framing analyses of coverage of specific ceasefires.** Content and framing studies of individual ceasefires exist (e.g. Murua and Ramírez de la Piscina's 2017 study of Basque and Spanish press coverage of the end of ETA's ceasefire). These are single-case, manual-coding, qualitative designs. They establish that ceasefires are covered and that coverage is framed strategically; they produce no time series, no decay rate, and no predictive test.
2. **Ceasefire effects on violence.** Clayton and Sticher (2021) and especially Lundgren, Svensson and Karakuş (2023) estimate the effect of ceasefires on the intensity of armed violence using UCDP GED-type data. They measure the *violence* response to ceasefires, not the *attention* response, and they use violence — not attention — to predict survival.
3. **Media attention as a cause of peace/conflict duration.** Burgoon et al. (2015) show that media reporting on human rights abuses is associated with shorter conflicts and negotiated agreements, adjudicating between "naming and shaming" and intransigence mechanisms. This is the most important adjacent finding for us: it establishes that media attention and conflict termination are linked. But it uses *volume of human-rights reporting* as an aggregate explanatory variable for conflict duration; it does not measure post-ceasefire decay, does not construct a half-life, and does not test attention as a predictor of ceasefire collapse.
4. **Attention as an allocative force in humanitarian response.** Eisensee and Strömberg (2007) and Hawkins (2011) establish that attention to conflict and disaster is selective and consequential.
5. **Attention decay as an estimable quantity in other domains.** Candia et al. (2019), Lorenz-Spreen et al. (2019), Parolo et al. (2015), Pfeffer and Matter (2023), Wu and Huberman (2007), Yang and Leskovec (2011).

### 4.2 What DOES NOT exist

To the best of our knowledge, after systematic searching (Section 4.3), **no published study**:

- **(a)** estimates a decay rate or half-life of public attention following **ceasefire announcements**, in any language or any medium;
- **(b)** uses **Wikipedia page views** (or any digital attention trace) as the measurement instrument for attention to armed conflict or peace processes;
- **(c)** treats **attention decay as a predictor of ceasefire collapse**, i.e. uses the *rate* of attention loss (rather than its level) as a leading indicator of the resumption of armed violence;
- **(d)** constructs a cross-lingual **war-versus-peace concept-attention ratio** (our WPAR), or any comparable normalised index contrasting attention to war concepts with attention to peace concepts;
- **(e)** links attention dynamics to UCDP GED-measured violence around ceasefire events at the event level across many conflicts.

### 4.3 How the negative claim was established (searched 2026-11-07)

Negative claims are only as good as the search behind them. The following were run and are reproducible:

- **OpenAlex** `title_and_abstract.search` co-occurrence filters: `"ceasefire" AND "Wikipedia"` returned 1 hit (an unrelated book chapter); `"ceasefire" AND "pageviews"` returned **0 hits**; `"ceasefire" AND "media attention"` returned 4 hits, **none** a quantitative attention-decay study (one economic-history paper, two 2026 non-peer-reviewed pieces, one student thesis).
- **OpenAlex** relevance searches on: *"ceasefire media attention public opinion"*, *"Wikipedia pageviews conflict war public interest"*, *"declining media attention to armed conflict"*, *"attention decay news event half-life"*, *"war peace attention ratio Wikipedia"*, *"public attention peace agreement durability"*. Top results were examined by title/venue; none was a study of attention decay around ceasefires.
- **Crossref** `query.title` and `query.bibliographic` searches on: *"media coverage ceasefire duration violence resumption"*, *"ceasefire announcement news coverage volume time series"*, *"attention to peace process media coverage decline negotiations"*, *"Google Trends Wikipedia attention Russia Ukraine war public interest decline"*.
- **Semantic Scholar** relevance search on *"ceasefire attention public opinion media"* and related strings.
- **Citation-chain checks**: the reference lists/abstracts of the two most recent reviews in the area (Bara, Clayton and Rustad, 2021; Hultman and Mousa, 2025) were inspected for attention or media variables — Hultman and Mousa's review of peacemaking and peacebuilding evidence is organised around violence reduction and intergroup attitudes, with no attention- or media-based predictor in its framework.

**Limits of the negative claim.** It is a claim about the *published, indexed* literature up to November 2026, not a proof of absence. Preprints, non-English scholarship, NGO/practitioner monitoring reports, and very recent working papers may exist outside these indexes. We should therefore write "we are not aware of any study that…" rather than "no study has ever…", and we should say in the paper exactly which databases we searched.

### 4.4 Consequence: we must adopt, not reinvent, the outcome

Because Clayton and Sticher (2021) already model ceasefire survival using UCDP GED conflict deaths, and Lundgren et al. (2023) already estimate ceasefire effects on violence intensity, **our outcome variable is not novel and must not be presented as such.** We should adopt a standard operationalisation (e.g. violence intensity exceeding a pre-specified threshold within a fixed window, following these papers) and be explicit that our contribution is the *predictor*, not the outcome.

---

## 5. Gap statement

**Paragraph 1 — what is established.** Two literatures meet at our problem but have never been joined. On one side, a mature quantitative literature has established that collective attention to events and topics decays in a regular, estimable way, decomposable into a fast communicative component and a slow cultural one (Candia et al., 2019), that this decay is accelerating (Lorenz-Spreen et al., 2019), and that such decay rates are meaningful, field-varying parameters (Parolo et al., 2015; Pfeffer and Matter, 2023). On the other side, the study of ceasefires has matured rapidly: we now have a population-level ceasefire dataset covering 2,202 ceasefires (Clayton et al., 2022), a theory of ceasefire design and survival tested against georeferenced fatality data (Clayton and Sticher, 2021), event-level estimates of ceasefire effects on violence intensity (Lundgren et al., 2023), and a well-developed account of which structural features make settlements durable — peacekeeping, credible commitment, power-sharing, mediation (Fortna, 2004, 2008; Walter, 2002; Hartzell and Hoddie, 2003; Beardsley, 2011).

**Paragraph 2 — what is missing.** What is missing is any measurement of *how fast public attention leaves a ceasefire*, and any test of whether that rate matters. Prior work on attention to conflict is either qualitative and single-case (framing studies of individual ceasefires), or measures attention as a *level* rather than a *rate* (Burgoon et al., 2015, on human-rights reporting and conflict duration), or studies attention's allocative consequences without estimating decay (Eisensee and Strömberg, 2007; Hawkins, 2011). Prior work on ceasefire durability is uniformly structural and violence-based: in the entire durability and ceasefire-survival literature, public attention appears nowhere as a variable. And the one data source that could measure attention at the required resolution, Wikipedia page views, has been validated for elections, markets, disease, disasters and cultural memory (Moat et al., 2013; McIver and Brownstein, 2014; García-Gavilanes et al., 2017; Ruprechter et al., 2023) but never for armed conflict or peace. We searched OpenAlex, Crossref and Semantic Scholar and found zero studies measuring attention decay around ceasefires, and zero studies using Wikipedia page views for conflict attention (Section 4.3).

**Paragraph 3 — what is therefore novel, precisely.** Our contribution is not a new estimator, a new dataset of ceasefires, or a new theory of durability; each of those exists. It is four specific conjunctions. **(1)** PAHL — the transfer of an established bi-exponential decay estimator (Candia et al., 2019) to *ceasefire announcements* as a new event class, producing the first estimates of an attention half-life for peace. **(2)** WPAR — a normalised, *cross-lingual* ratio of war-concept to peace-concept attention, which is new in two respects: no prior work constructs a war/peace attention contrast at all, and no prior work does so across ~12 language editions, though the feasibility of cross-lingual Wikipedia attention comparison is established (Ruprechter et al., 2023; Gildersleeve and Lambiotte, 2023). **(3)** The *predictive* claim — that the decay rate, not the level, of attention predicts ceasefire collapse as measured by UCDP GED — which inverts the existing causal direction (attention as consequence of violence) and is, as far as we can determine, untested. **(4)** The wedding of these to a standard, non-novel violence-based outcome, which lets us ask a genuinely new question — *does the world's attention to a peace deal predict whether the deal holds?* — while remaining comparable to, and falsifiable against, the existing durability literature.

**A short, honest version for the abstract:** *We are not aware of any study that measures how fast public attention decays after a ceasefire, or that tests whether that decay rate predicts the resumption of violence. Existing work measures either attention to conflict as a level (not a rate) or ceasefire durability from structural and violence variables (not attention). We estimate an attention half-life for each of ~40 ceasefires across ~12 Wikipedia language editions and test it against UCDP GED violence.*

---

## 6. Bibliography

*Format: Author (Year). Title. Venue. URL. All entries verified against Crossref/OpenAlex records; all URLs resolved during preparation.*

- Åkebo, M. (2016). Ceasefire Agreements and Peace Processes: A Comparative Study. Routledge. https://doi.org/10.4324/9781315562360
- Bara, C., Clayton, G., & Aas Rustad, S. (2021). Understanding Ceasefires. International Peacekeeping, 28(3), 329–340. https://doi.org/10.1080/13533312.2021.1926236
- Baum, M. A. (2002). The Constituent Foundations of the Rally-Round-the-Flag Phenomenon. International Studies Quarterly, 46(2), 263–298. https://doi.org/10.1111/1468-2478.00232
- Baum, M. A., & Potter, P. B. K. (2008). The Relationships Between Mass Media, Public Opinion, and Foreign Policy: Toward a Theoretical Synthesis. Annual Review of Political Science, 11, 39–65. https://doi.org/10.1146/annurev.polisci.11.060406.214132
- Baumgartner, F. R., & Jones, B. D. (1993). Agendas and Instability in American Politics. University of Chicago Press. https://openlibrary.org/works/OL2734294W
- Beardsley, K. (2011). The Mediation Dilemma. Cornell University Press. https://doi.org/10.7591/9780801462610
- Bell, C., & Badanjak, S. (2019). Introducing PA-X: A new peace agreement database and dataset. Journal of Peace Research, 56(3), 452–466. https://doi.org/10.1177/0022343318819123
- Bell, C., Badanjak, S., et al. (2024). PA-X Peace Agreements Database. University of Edinburgh. https://www.peaceagreements.org/
- Burgoon, B., Ruggeri, A., Schudel, W., & Manikkalingam, R. (2015). From Media Attention to Negotiated Peace: Human Rights Reporting and Civil War Duration. International Interactions, 41(2), 226–255. https://doi.org/10.1080/03050629.2014.942898
- Candia, C., Jara-Figueroa, C., Rodriguez-Sickert, C., Barabási, A.-L., & Hidalgo, C. A. (2019). The universal decay of collective memory and attention. Nature Human Behaviour, 3, 82–91. https://doi.org/10.1038/s41562-018-0474-5
- Chadefaux, T. (2014). Early warning signals for war in the news. Journal of Peace Research, 51(1), 5–18. https://doi.org/10.1177/0022343313507302
- Ciampaglia, G. L., Flammini, A., & Menczer, F. (2015). The production of information in the attention economy. Scientific Reports, 5, 9452. https://doi.org/10.1038/srep09452
- Clayton, G., Nathan, L., & Wiehler, C. (2021). Ceasefire Success: A Conceptual Framework. International Peacekeeping, 28(3), 341–365. https://doi.org/10.1080/13533312.2021.1894934
- Clayton, G., Nygård, H. M., Rustad, S. A., & Strand, H. (2022). Introducing the ETH/PRIO Civil Conflict Ceasefire Dataset. Journal of Conflict Resolution, 67(7–8), 1430–1451. https://doi.org/10.1177/00220027221129183
- Clayton, G., & Sticher, V. (2021). The Logic of Ceasefires in Civil War. International Studies Quarterly, 65(3), 633–646. https://doi.org/10.1093/isq/sqab026
- Davies, S., Pettersson, T., & Öberg, M. (2022). Organized violence 1989–2021 and drone warfare. Journal of Peace Research, 59(4), 593–610. https://doi.org/10.1177/00223433221108428
- Downs, A. (1972). Up and Down with Ecology: The "Issue-Attention Cycle". The Public Interest, 28, 38–50. (Reprinted in Agenda Setting, Routledge, 2016.) https://doi.org/10.4324/9781315538389-9
- Eisensee, T., & Strömberg, D. (2007). News Droughts, News Floods, and U.S. Disaster Relief. The Quarterly Journal of Economics, 122(2), 693–728. https://doi.org/10.1162/qjec.122.2.693
- Fortna, V. P. (2004). Does Peacekeeping Keep Peace? International Intervention and the Duration of Peace After Civil War. International Studies Quarterly, 48(2), 269–292. https://doi.org/10.1111/j.0020-8833.2004.00301.x
- Fortna, V. P. (2008). Does Peacekeeping Work? Shaping Belligerents' Choices after Civil War. Princeton University Press. https://openlibrary.org/works/OL5725343W
- Galtung, J., & Ruge, M. H. (1965). The Structure of Foreign News: The Presentation of the Congo, Cuba and Cyprus Crises in Four Norwegian Newspapers. Journal of Peace Research, 2(1), 64–90. https://doi.org/10.1177/002234336500200104
- García-Gavilanes, R., Mollgaard, A., Tsvetkova, M., & Yasseri, T. (2017). The memory remains: Understanding collective memory in the digital age. Science Advances, 3(4), e1602368. https://doi.org/10.1126/sciadv.1602368
- García-Gavilanes, R., Tsvetkova, M., & Yasseri, T. (2016). Dynamics and biases of online attention: the case of aircraft crashes. Royal Society Open Science, 3(10), 160460. https://doi.org/10.1098/rsos.160460
- Gilboa, E. (2005). The CNN Effect: The Search for a Communication Theory of International Relations. Political Communication, 22(1), 27–44. https://doi.org/10.1080/10584600590908429
- Gildersleve, P., Lambiotte, R., & Yasseri, T. (2023). Between news and history: identifying networked topics of collective attention on Wikipedia. Journal of Computational Social Science, 6(2), 845–875. https://doi.org/10.1007/s42001-023-00215-w
- Hartzell, C., & Hoddie, M. (2003). Institutionalizing Peace: Power Sharing and Post-Civil War Conflict Management. American Journal of Political Science, 47(2), 318–332. https://doi.org/10.1111/1540-5907.00022
- Hartzell, C., Hoddie, M., & Rothchild, D. (2001). Stabilizing the Peace After Civil War: An Investigation of Some Key Variables. International Organization, 55(1), 183–208. https://doi.org/10.1162/002081801551450
- Hawkins, V. (2011). Media selectivity and the other side of the CNN effect: the consequences of not paying attention to conflict. Media, War & Conflict, 4(1), 55–68. https://doi.org/10.1177/1750635210396126
- Hegre, H., Allansson, M., Basedau, M., et al. (2019). ViEWS: A political violence early-warning system. Journal of Peace Research, 56(2), 155–174. https://doi.org/10.1177/0022343319823860
- Hultman, L. (2010). Keeping Peace or Spurring Violence? Unintended Effects of Peace Operations on Violence against Civilians. Civil Wars, 12(1–2), 29–46. https://doi.org/10.1080/13698249.2010.484897
- Hultman, L., Kathman, J., & Shannon, M. (2013). United Nations Peacekeeping and Civilian Protection in Civil War. American Journal of Political Science, 57(4), 875–891. https://doi.org/10.1111/ajps.12036
- Hultman, L., & Mousa, S. (2025). From ceasefire to cohesion: An integrated review of peacemaking and peacebuilding. Economic Policy, 40(124), 931–967. https://doi.org/10.1093/epolic/eiaf011
- Jones, B. D., & Baumgartner, F. R. (2005). The Politics of Attention: How Government Prioritizes Problems. University of Chicago Press. https://openlibrary.org/works/OL21001565W
- Karakuş, D. C., & Svensson, I. (2017). Between the Bombs: Exploring Partial Ceasefires in the Syrian Civil War, 2011–2017. Terrorism and Political Violence, 32(4), 681–700. https://doi.org/10.1080/09546553.2017.1393416
- Kinnick, K. N., Krugman, D. M., & Cameron, G. T. (1996). Compassion Fatigue: Communication and Burnout toward Social Problems. Journalism & Mass Communication Quarterly, 73(3), 687–707. https://doi.org/10.1177/107769909607300314
- Kogen, L., & Price, M. E. (2011). Deflecting the CNN effect: public opinion polling and Livingstonian outcomes. Media, War & Conflict, 4(2), 109–123. https://doi.org/10.1177/1750635211406051
- Kreutz, J. (2010). How and when armed conflicts end: Introducing the UCDP Conflict Termination dataset. Journal of Peace Research, 47(2), 243–250. https://doi.org/10.1177/0022343309353108
- Lehmann, J., Gonçalves, B., Ramasco, J. J., & Cattuto, C. (2012). Dynamical classes of collective attention in Twitter. Proceedings of the 21st International Conference on World Wide Web (WWW '12), 251–260. https://doi.org/10.1145/2187836.2187871
- Livingston, S., & Eachus, T. (1995). Humanitarian crises and U.S. foreign policy: Somalia and the CNN effect reconsidered. Political Communication, 12(4), 413–429. https://doi.org/10.1080/10584609.1995.9963087
- Lorenz-Spreen, P., Mønsted, B. M., Hövel, P., & Lehmann, S. (2019). Accelerating dynamics of collective attention. Nature Communications, 10, 1759. https://doi.org/10.1038/s41467-019-09311-w
- Lundgren, M., Svensson, I., & Karakuş, D. C. (2023). Local Ceasefires and De-escalation: Evidence From the Syrian Civil War. Journal of Conflict Resolution, 67(7–8), 1350–1375. https://doi.org/10.1177/00220027221148655
- McCombs, M. E., & Shaw, D. L. (1972). The Agenda-Setting Function of Mass Media. Public Opinion Quarterly, 36(2), 176–187. https://doi.org/10.1086/267990
- McIver, D. J., & Brownstein, J. S. (2014). Wikipedia Usage Estimates Prevalence of Influenza-Like Illness in the United States in Near Real-Time. PLoS Computational Biology, 10(4), e1003581. https://doi.org/10.1371/journal.pcbi.1003581
- Moat, H. S., Curme, C., Avakian, A., Kenett, D. Y., Stanley, H. E., & Preis, T. (2013). Quantifying Wikipedia Usage Patterns Before Stock Market Moves. Scientific Reports, 3, 1801. https://doi.org/10.1038/srep01801
- Moeller, S. D. (1999). Compassion Fatigue: How the Media Sell Disease, Famine, War and Death. Routledge. https://www.routledge.com/Compassion-Fatigue-How-the-Media-Sell-Disease-Famine-War-and-Death/Moeller/p/book/9780415920476
- Mueller, H., & Rauh, C. (2018). Reading Between the Lines: Prediction of Political Violence Using Newspaper Text. American Political Science Review, 112(2), 358–375. https://doi.org/10.1017/S0003055417000570
- Mueller, J. E. (1970). Presidential Popularity from Truman to Johnson. American Political Science Review, 64(1), 18–34. https://doi.org/10.2307/1955610
- Murua, I., & Ramírez de la Piscina, T. (2017). Ceasefire as bad news: the coverage of the end of ETA in the Basque and Spanish press. Revista Latina de Comunicación Social, 72. https://doi.org/10.4185/RLCS-2017-1228
- Parolo, P. D. B., Pan, R. K., Ghosh, R., Huberman, B. A., Kaski, K., & Fortunato, S. (2015). Attention decay in science. Journal of Informetrics, 9(4), 734–745. https://doi.org/10.1016/j.joi.2015.07.006
- Pfeffer, J., Matter, D., & Sargsyan, A. (2023). The Half-Life of a Tweet. Proceedings of the International AAAI Conference on Web and Social Media, 17, 1163–1167. https://doi.org/10.1609/icwsm.v17i1.22228
- Robinson, P. (1999). The CNN effect: can the news media drive foreign policy? Review of International Studies, 25(2), 301–309. https://doi.org/10.1017/S0260210599003010
- Roediger, H. L., & Abel, M. (2015). Collective memory: a new arena of cognitive study. Trends in Cognitive Sciences, 19(7), 359–361. https://doi.org/10.1016/j.tics.2015.04.003
- Ruprechter, T., Burghardt, K., & Helic, D. (2023). Poor attention: The wealth and regional gaps in event attention and coverage on Wikipedia. PLoS ONE, 18(11), e0289325. https://doi.org/10.1371/journal.pone.0289325
- Spoerri, A. (2007). What is popular on Wikipedia and why? First Monday, 12(4). https://doi.org/10.5210/fm.v12i4.1765
- Sticher, V. (2022). Ceasefire Violations: Why They Occur and How They Relate to Strategic Decision-Making Processes. International Studies Review, 24(4), viac046. https://doi.org/10.1093/isr/viac046
- Sundberg, R., & Melander, E. (2013). Introducing the UCDP Georeferenced Event Dataset. Journal of Peace Research, 50(4), 523–532. https://doi.org/10.1177/0022343313484347
- Tizzoni, M., Panisson, A., Paolotti, D., & Cattuto, C. (2020). The impact of news exposure on collective attention in the United States during the 2016 Zika epidemic. PLoS Computational Biology, 16(3), e1007633. https://doi.org/10.1371/journal.pcbi.1007633
- Uppsala Conflict Data Program (2024). UCDP Georeferenced Event Dataset (GED). Uppsala University. https://ucdp.uu.se/ged/
- Walter, B. F. (2002). Committing to Peace: The Successful Settlement of Civil Wars. Princeton University Press. https://doi.org/10.1515/9781400824465
- Ward, M. D., Greenhill, B., & Bakke, K. M. (2010). The perils of policy by p-value: Predicting civil conflicts. Journal of Peace Research, 47(4), 363–375. https://doi.org/10.1177/0022343309356491
- Wikimedia Foundation (2024). Wikimedia Analytics API: Pageviews. https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/
- Wu, F., & Huberman, B. A. (2007). Novelty and collective attention. Proceedings of the National Academy of Sciences, 104(45), 17599–17601. https://doi.org/10.1073/pnas.0704916104
- Yang, J., & Leskovec, J. (2011). Patterns of temporal variation in online media. Proceedings of the Fourth ACM International Conference on Web Search and Data Mining (WSDM '11), 177–186. https://doi.org/10.1145/1935826.1935863
- Yasseri, T., & Bright, J. (2016). Wikipedia traffic data and electoral prediction: towards theoretically informed models. EPJ Data Science, 5, 22. https://doi.org/10.1140/epjds/s13688-016-0083-3
- Yasseri, T., Sumi, R., Rung, A., Kornai, A., & Kertész, J. (2012). Dynamics of Conflicts in Wikipedia. PLoS ONE, 7(6), e38869. https://doi.org/10.1371/journal.pone.0038869

---

## Appendix A. Items I could not verify (excluded from Sections 1–5 and from the bibliography)

These were named in the project brief or surfaced during searching but could not be confirmed to exist as described. **Do not cite them without independent verification.**

- **"Jones" on "hidden emergencies."** The brief refers to work on "hidden emergencies" attributed to Jones. I could not locate any published work by an author named Jones with that title or concept in Crossref, OpenAlex or Crossref bibliographic search. Searches for `"hidden emergencies" media coverage humanitarian crises` returned only unrelated medical-humanitarian items. **Status: UNVERIFIED — cut.** Substitutes that make the same argument with verifiable sources: Hawkins (2011) on ignored conflicts and unchecked death tolls; Kinnick et al. (1996) and Moeller (1999) on compassion fatigue; Franks (2006) on the CARMA report on Western media coverage of humanitarian disasters (verified to exist: *The Political Quarterly*, 77(1), doi:10.1111/j.1467-923X.2006.00771.x) — worth adding if a media-studies anchor is needed.
- **"Kogen" (2021/2015) on media and humanitarian crises.** The citation as given in the brief does not resolve. The verifiable Kogen work is **Kogen and Price (2011)**, on polling and Livingstonian outcomes, which is cited in Section 1.3. There is no verified Kogen paper on attention decay or on ceasefire coverage.
- **Lehmann et al. on Wikipedia and influenza.** Frequently mis-cited. The Wikipedia flu-surveillance paper is **McIver and Brownstein (2014)**, not Lehmann et al.; it is cited correctly in Section 3. (Lehmann et al. 2012 is a different paper, on Twitter attention dynamics.)
- **Downs (1972) original PDF.** The original appeared in *The Public Interest* 28: 38–50, which has no stable DOI. The URL given is the verified Routledge reprint chapter (2016), and the entry says so. If a direct original is required, obtain it from a library archive rather than an unverified PDF.
- **Exact page ranges** for a small number of entries (marked by volume/issue only, e.g. Hultman and Mousa 2025; Clayton et al. 2022) are from the publisher record and may need a final check against the printed version.
