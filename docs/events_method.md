# Ceasefire event table: method

Project: *The Half-Life of Peace*. Dataset: `data/events/ceasefires.csv` (36 events, 2015-2025, 20 theatre countries). Metadata and field definitions: `data/events/ceasefires_metadata.json`. Curated and verified 2026-11-07.

## 1. What the table is for

The table supplies t=0 for an event-study of public attention. Each row is a dated public announcement, signature, or entry into force of a suspension of hostilities. It is deliberately *not* a census: a salience-weighted sample large enough for a half-life estimate and diverse enough for a survival-style test. Because attention is aligned at t=0, date correctness matters more than breadth.

## 2. Inclusion criteria

An event enters if all of the following hold:

1. It is a ceasefire, truce, cessation of hostilities, humanitarian pause, de-escalation arrangement, or a peace agreement containing a ceasefire, announced between 2015-01-01 and 2025-11-07.
2. It is a discrete, dated event — an announcement, signature, or entry into force — rather than a standing negotiation process.
3. At least one authoritative page states the recorded date, **and the curator opened that page and read the sentence**.
4. The event was salient enough to be plausibly measurable in multilingual Wikipedia pageviews.
5. The theatre country is covered by UCDP GED where possible, so the analyst can derive the outcome.

## 3. Exclusion criteria

- Outside the window (Israel-Hamas 2012 and 2014 were left out as out-of-window controls).
- Date could not be pinned to one authoritative page: dropped rather than guessed (e.g. the Myanmar China-mediated northern Shan ceasefire, reported as both 14 Dec 2023 and 11 Jan 2024).
- Routine local truces (hundreds per year, invisible in global attention data).
- Unilateral declarations repudiated within days and never functioning as a cessation.
- Instruments with no cessation-of-hostilities component (grain corridors, prisoner exchanges).
- Duplicate coverage of the same conflict and news cycle (only one Philippines 2016 row is kept, although Duterte declared twice).

## 4. Classification scheme

**agreement_type** — `ceasefire` (stop of military operations with a stated effective time and theatre; 24 rows); `peace_agreement` (signed settlement including a ceasefire plus political/security provisions; 7); `humanitarian_pause` (temporary suspension framed around aid or hostage release, typically days; 2); `de-escalation` (front-line freeze or zone/withdrawal arrangement without a full ceasefire; 2); `truce` (short, renewable suspension; 1).

**geographic_scope** — `national`, `regional` (cross-border), `subnational` (province, governorate, enclave, de-escalation zone): the reach of the *commitment*, not of the conflict.

**headline_salience** — curator's ex-ante estimate of expected global coverage: `high` (18), `medium` (13), `low` (5); a design covariate with measurement error, not observed data.

**Outcomes are deliberately not encoded.** `held_12m` is the analyst's variable, derived from UCDP GED with the pre-registered threshold. Notes record implementation observations only to aid review; they are not the label.

## 5. Date conventions and contested dates

Preference order: (1) entry-into-force date where stated; (2) signature/announcement date where no effective time is given; (3) conclusion date where that is all there is. The convention used is in every row's notes. Six events have contested dates:

- Minsk II — agreed 12 Feb 2015, effective 15 Feb (15 Feb recorded).
- CAR Khartoum — initialled 5 Feb 2019, signed 6 Feb (5 Feb recorded).
- Sudan Juba — initialled 31 Aug 2020, signed 3 Oct (31 Aug recorded).
- Yemen Stockholm — concluded 13 Dec 2018, Hudaydah effective 18 Dec (13 Dec recorded, as the cited page states).
- Sudan Jeddah — signed 20 May 2023, in force 22 May (20 May recorded).
- Mali Algiers — signed 15 May and 20 Jun 2015 (20 Jun recorded, completing signatures).

## 6. Verification standard

One authoritative source fetch per event was the budget rule. For each row the curator fetched a page, extracted its body text, and confirmed a sentence containing the recorded date; that context was written into `notes`. No date was accepted from a search snippet alone, and no URL was constructed from memory. `verified=TRUE` means exactly that check; all 36 rows carry it.

Source preference: UN (UN News, UNSMIL, UNMHA, OSESGY, OSESG-Syria, OCHA), OSCE, African Union, official government statements (Kremlin, Turkish MFA, Indian PIB, Philippine OPAPRU, Malaysian MFA, Myanmar MOI), then wire services (TASS, Xinhua) where the institutional page was unreachable. Reuters and AP pages blocked automated retrieval and are not cited.

## 7. Known weaknesses

1. **Curation judgment at the event boundary.** Syria has five rows and Colombia one, so row counts over-weight some conflicts; cross-conflict analysis should weight by conflict.
2. **Wire-service fallback.** Seven rows rely on TASS or Xinhua where the institutional page was unreachable; the date was still read on the page, but these are state agencies.
3. **Salience is a judgment**, not a measurement. **Midnight effects**: local effective times near midnight can shift the calendar date by a day versus some reporting.
4. **No UCDP ids.** `ucdp_dyad_id`/`ucdp_conflict_id` are blank rather than guessed; join on country, conflict name and date window with manual dyad review.
5. **English-language skew** in sourcing, partly mitigated by Arabic UN News, the Angolan public broadcaster and Myanmar's ministry pages.
