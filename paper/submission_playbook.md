# Submission playbook: from finished manuscript to indexed preprint

A practical, step-by-step guide for getting *The Half-Life of Peace* (a) on the
open web with a persistent identifier, (b) picked up by Google Scholar, and (c)
discoverable by the humans who might actually read a paper about ceasefire
attention. It is written for an independent researcher with no institutional
library, no journal editor, and no budget.

The honest summary up front: publication is not one act, it is three separable
ones. **Hosting** makes the PDF available at a stable URL. **Identification**
gives it a DOI and correct metadata so machines can find and disambiguate it.
**Indexing** is a crawler deciding to include it in Google Scholar, and you
cannot submit to that decision directly. Doing all three, in that order, is what
makes a preprint findable. Uploading to ResearchGate alone does none of them
well.

---

## 0. The 30-minute minimum viable path

If you only ever do four things, do these, in this order:

- [ ] Put the code and data on GitHub with a tagged release and a `CITATION.cff`.
- [ ] Archive that release on Zenodo to get a DOI (Section 2).
- [ ] Post the PDF on **SocArXiv** (free, fast, social-science repository, Crossref DOI) or **SSRN** (Section 5).
- [ ] Create a Google Scholar profile and add the paper manually, using the same name form everywhere (Section 4).

That combination gets a DOI, a stable URL on a crawled repository, and correct
author metadata. Everything else in this document improves the odds; this set
establishes them.

---

## 1. Before you upload anything: pre-flight

The single most common reason a preprint is never indexed is that the PDF is
unusable by a crawler or the metadata is inconsistent. Fix this once.

**The PDF itself**

- [ ] Text, not images. Run `pdftotext paper.pdf - | head -50` (or open and
      select-copy). If the title and abstract do not come out as selectable
      text, re-export. Scholar cannot index a scanned page.
- [ ] First page contains, as text: the full title, the author's name, an
      affiliation (if any), the date, and the abstract. Do not put the title
      only in a decorative image.
- [ ] Filename is descriptive and stable: `Jaffar_2026_Half-Life-of-Peace.pdf`.
      The filename becomes part of the URL on most servers and is a small but
      real signal.
- [ ] The PDF's embedded `Title` metadata matches the paper title exactly. With
      pandoc this comes from the YAML `title:` field; check it with
      `pdfinfo paper.pdf | grep Title` or `exiftool paper.pdf`.
- [ ] No password, no DRM, no "download requires login", no CAPTCHA in front of
      the file. Scholar's crawler is blocked by all three.
- [ ] Consistent author name. Pick one form - `Ahmed Jaffar` - and use it in the
      PDF, on every repository, in `CITATION.cff`, on ResearchGate, and in your
      Scholar profile. Variants (`A. Jaffar`, `Ahmed K. Jaffar`) create duplicate
      author records and split citations.

**The repository**

- [ ] Public GitHub repo, with `README.md`, `LICENSE`, `CITATION.cff`, and a
      frozen data or retrieval path so the result can be checked.
- [ ] A tagged release (`v0.1.0`) that exactly matches the manuscript's numbers
      and the version of the code you ran.
- [ ] `CITATION.cff` with `title`, `authors`, `repository-code`, `license`,
      `version`, `date-released`, `keywords`, and `abstract`. GitHub renders it
      as a "Cite this repository" button, and Zenodo reads it.

**The manuscript text**

- [ ] Title, abstract, and keywords final. Changing the title after indexing
      splits the record and loses citations; this is the one thing to get right
      before the first upload.
- [ ] Abstract is 150-250 words for the manuscript, but **shorter versions**
      (often 1,000-1,500 *characters* with spaces) are demanded by arXiv, SSRN,
      and ResearchGate. Prepare three: a 250-word version, a 150-word version,
      and a 60-word one-liner.
- [ ] Keywords are chosen for how a reader would search, not how a sociologist
      would classify: `ceasefire durability`, `attention decay`, `Wikipedia
      pageviews`, `conflict early warning`, `peace agreements`. For this paper,
      the JEL codes `D74` (conflict; conflict resolution; alliances), `D83`
      (search; learning; information), and `F51` (international conflicts) fit
      SSRN and SocArXiv categories well. arXiv primary category `cs.SI` (Social
      and Information Networks), cross-list `econ.GN` (General Economics).

---

## 2. A DOI in practice: Zenodo

A DOI is not required to be indexed, but it is the cheapest insurance against
link rot and the most reliable way to make one paper citable as one object. It
also lets you cite "the dataset" and "the code" separately from "the paper",
which reviewers of a computational paper increasingly expect.

Zenodo is the right default for an independent researcher: free, no
institutional requirement, run by CERN, mints DataCite DOIs, and integrates
directly with GitHub.

**Step-by-step, with GitHub integration (recommended)**

1. Sign in at <https://zenodo.org> with GitHub (or ORCID, or email).
2. Go to *Settings -> GitHub*. Zenodo lists your public repositories. Flip the
   switch on for the paper repository. This installs a webhook; nothing is
   uploaded yet.
3. On GitHub, create a **release**, not just a commit: *Releases -> Draft a new
   release*, tag it `v0.1.0`, give it a title, and describe what is frozen.
4. Publishing the release triggers Zenodo. Within seconds a draft record appears
   under *Upload* (or `zenodo.org/account/settings/github/`). Zenodo takes its
   metadata from `CITATION.cff` if present, otherwise from the repo.
5. **Edit the draft before publishing.** This is the step people skip and
   regret. Set: title, author(s) with ORCID if you have one, publication date,
   description/abstract, keywords, license (CC BY 4.0 for the paper; MIT for
   code if the record is the code), language, and the resource type
   (`Publication -> Preprint` for the paper record).
6. Click **Publish**. The record is immutable after publishing; you can publish
   a new version later, which gets a new version DOI.
7. Record two DOIs from the record page: the **version DOI** (this release) and
   the **concept DOI** (all versions, always resolves to the latest). Cite the
   version DOI in the paper's own "how to cite" note and put the concept DOI in
   your README. Never put a version DOI in a place where the pointer should stay
   current.
8. Add the DOI to the GitHub release notes and to `CITATION.cff` (`doi:` field)
   so future readers land in the right place.

**If you do not want GitHub integration:** use the manual upload form
(*New upload*), upload the PDF plus a zip of the code, and fill the same
metadata fields. You get the same DOI; you lose only the automatic archiving.

**Why this matters for finding the paper.** Google Scholar treats repositories
and open PDFs as first-class sources, and it resolves DOI landing pages. A
Zenodo record gives you: a persistent URL that never dies, a citation with an
"Cited by" count, a citable object for the dataset, and inclusion in DataCite's
metadata graph, which feeds OpenAlex, Semantic Scholar, and many library
catalogues even when Scholar itself is slow to pick it up. A DOI does not
guarantee Scholar inclusion - nothing does - but it removes every structural
reason for exclusion except the crawler's own decisions.

---

## 3. ResearchGate: what it is for, and what it is not for

ResearchGate is a professional network with a papers section. It is genuinely
useful for people finding your work through their network and for the
"request full text" flow. It is **not** a preprint server in the indexing sense:
ResearchGate does not supply metadata to Google Scholar, and a paper that exists
only on ResearchGate is routinely absent from Scholar results. Treat it as a
distribution channel, not as a publication of record.

**Upload steps**

1. Create an account and fill the profile: real name in one consistent form,
   affiliation ("Independent researcher" is acceptable), research interests.
2. Click *Add new -> Publication*, or go to your profile and use *Add
   publication*.
3. Choose *Upload file*. Upload the PDF.
4. Fill the metadata form. RG asks for type (*Preprint* or *Article* - choose
   *Preprint* and be honest about it), title, authors, publication date,
   abstract, keywords, and the DOI if you have one (put the Zenodo DOI here).
5. Publish. RG assigns an internal publication page URL.
6. Link the duplicate: if RG already auto-imported the paper from Crossref or
   another source, claim the existing record instead of making a second one.
   Duplicate RG records split views and look sloppy.

**The institutional-email constraint.** RG strongly pushes verification with an
institutional email address, and some features (author profile claiming,
"verified" status, certain messaging) are gated behind it. If you do not have
one: you can still create an account with a personal email and still upload and
share papers; what you lose is the verified badge and some network features.
Workarounds that actually help are limited but real - if you have any
university affiliation, even an old alumni address or a visiting appointment,
that is usually sufficient to verify. Do not fabricate an affiliation. The
paper's credibility is worth more than a badge.

**One more honest point.** RG engagement (reads, followers) is not a citation
metric and should not be optimised for. Upload, fill the metadata, and leave it.

---

## 4. Google Scholar: how it actually works

There is no "submit to Google Scholar" button for an individual paper. Scholar
is a crawler. It discovers scholarly documents by crawling the open web,
repository platforms, and publisher sites that follow its inclusion guidelines,
and it therefore indexes PDFs it can fetch, parse, and attribute to an author.

What Scholar can do, and where you can influence it:

**A. Repository placement is the main lever.** Scholar crawls the preprint and
institutional repository ecosystem. Posting to a recognised repository (SSRN,
SocArXiv via OSF Preprints, arXiv, or an institutional repository) is the
strongest single action. Zenodo helps but is generalist; the preprint networks
are the ones Scholar expects to find papers on.

**B. Make the PDF machine-readable.** Full text, first page carrying title and
author, embedded PDF title metadata, stable URL, no login wall, `robots.txt`
that permits crawling. Scholar also supports Highwire-style citation meta tags
(`citation_title`, `citation_author`, `citation_publication_date`,
`citation_pdf_url`) on landing pages; repository platforms already emit these,
which is another reason to use a repository rather than a personal site.

**C. If you host on your own site**, you can ask Scholar to include the site:
Scholar's inclusion page (<https://scholar.google.com/intl/en/scholar/inclusion.html>)
offers a "include this website" request for a site you administer, and it
documents the meta-tag requirements. This is a site-level request, not a
paper-level submission, and it is slow and sometimes ignored. Do it as a
supplement, never as the plan.

**D. Create a Google Scholar Citations profile.** This is how Scholar knows that
"N papers by Ahmed Jaffar" are yours, and it is how you get an author page,
alerts, and a clean citation count. Sign in with a Google account, go to
<https://scholar.google.com/citations>, and create a profile. Profile creation
generally requires email verification, and historically has required a
verified institutional address; availability of other verification routes
changes over time, so if you are blocked, do not fake an institutional
affiliation - you can still be indexed as an author without a profile, and the
profile can be created later if you gain an institutional email. Once the
profile exists:

- Add the paper manually (*Add -> Add article manually*) if it has not been
  auto-claimed. Enter title, authors, venue ("Preprint"), year, and the DOI or
  the repository URL.
- Set your name exactly as it appears on the paper, and add alternate spellings
  under *Edit -> Name* so future records merge into the same profile.
- Turn on email alerts for new citations and for new papers by authors in your
  field.

**E. Timing.** Indexing is not instant. A new repository record often appears in
Scholar within days to a few weeks; Zenodo-only records can take longer or never
appear as a Scholar record (they remain discoverable through DataCite, OpenAlex,
and Semantic Scholar). Check with:

```
site:your-repository.org "Half-Life of Peace"
"Half-Life of Peace" Jaffar
```

If it is absent after 4-6 weeks, the usual causes are: the PDF was behind a
download button, the metadata was inconsistent, the repository is not crawled,
or the title on the PDF differs from the title in the record. Fix those, do not
re-upload duplicates.

---

## 5. arXiv, and what to do about the endorsement problem

arXiv is the best-distribution preprint server for computational social
science, and its records are crawled by everyone. The obstacle is endorsement:
first submissions to many categories require an endorsement from an established
arXiv author, unless your email domain is on arXiv's list of accepted
institutions. As an independent researcher you will likely not be
auto-endorsed.

Options, in descending order of usefulness:

1. **Get endorsed.** If you know any arXiv author in `cs.SI` or `econ.GN`, they
   can endorse you: arXiv gives every author a small endorsement quota, and the
   endorser enters your arXiv ID or email at the endorsement page. This is a
   normal, low-cost favour; ask directly and send the abstract.
2. **Post to SocArXiv instead.** Free, volunteer-moderated, Crossref DOI, social
   science focus, fast (usually 1-3 days). It is the best no-endorsement
   substitute for this paper, and Scholar crawls it. <https://socarxiv.xyz>
3. **Post to SSRN.** Free account, editorial screening (usually 1-5 business
   days), SSRN assigns a DOI (`10.2139/ssrn.XXXXXXX`), and the SSRN eLibrary is
   well indexed. Best fit: economics/policy working paper networks. Choose a
   relevant network (e.g. a Conflict/Peace economics or Political Economy
   network) at submission. SSRN's interface is dated and the metadata form is
   long; fill it carefully.
4. **Post to OSF Preprints.** Free, Crossref DOI (`10.31219/...`), permissive,
   good for interdisciplinary work; less prestigious than SSRN/arXiv.
5. **Zenodo as the record of last resort.** A DOI, a stable URL, and a citable
   object, but no moderation and weaker scholarly signalling.

Do not post the same version simultaneously to five servers. Pick one as the
record of record (SocArXiv or SSRN), add a Zenodo DOI for the code and data, and
cross-link them from the paper and the README. Duplicate records do not help
indexing and they make your citation count impossible to read.

---

## 6. Realistic 3-4 week timeline

Assume the manuscript is finished and the analysis is frozen. Times are for
someone with a day job.

**Week 0 - freeze (1-2 evenings)**

- [ ] Final read-through for numbers that changed after the analysis froze.
- [ ] Export the PDF; verify with `pdftotext` that title, abstract, and text are
      extractable.
- [ ] `pdfinfo` shows the intended Title; author name matches everywhere.
- [ ] GitHub release tagged; `CITATION.cff` updated with final title, keywords,
      abstract, DOI placeholder.
- [ ] Prepare the long (250-word), medium (150-word), and short (60-word)
      abstracts and the keyword list.
- [ ] Decide on authorship line and affiliation wording. Put the same string in
      every field on every platform.

**Week 1 - identity (2 evenings)**

- [ ] Zenodo/GitHub integration on; publish release; edit metadata carefully;
      publish the Zenodo record; note version DOI and concept DOI.
- [ ] Add the DOI to `CITATION.cff` and the README; commit and push.
- [ ] Optional: ORCID iD (free at <https://orcid.org>); add the paper's DOI to
      ORCID once it exists.

**Week 2 - hosting (2 evenings, plus moderation waiting time)**

- [ ] Submit to SocArXiv **or** SSRN (one of them as the record of record).
- [ ] If endorsable, submit to arXiv in parallel with the repository posting;
      the categories are `cs.SI` primary, `econ.GN` cross-list, `stat.AP`
      possible. arXiv's abstract field is plain text, no LaTeX.
- [ ] After moderation passes, the paper has a permanent URL. Put that URL in
      the GitHub README and in the Zenodo description.

**Week 3 - profiles and distribution (1 evening)**

- [ ] Upload to ResearchGate with the repository DOI in the DOI field.
- [ ] Create/complete a Google Scholar profile if your email situation allows;
      add the article manually with the repository URL.
- [ ] Add the paper to ORCID, Semantic Scholar author page (claim via
      <https://www.semanticscholar.org>), and OpenAlex (automatic from DOI;
      check it appears).
- [ ] Update the GitHub `CITATION.cff` one final time and post a short
      announcement where the relevant people are: a specialist mailing list, a
      conference, or a personal blog. One post, not a campaign.

**Week 4 - verify (30 minutes, then leave it)**

- [ ] Search Scholar for the exact title; if absent, check back in two weeks.
- [ ] Check the Crossref/DataCite metadata resolves: open the DOI URL.
- [ ] Check that `pdftotext` on the *served* PDF (from the repository URL) still
      shows the title. Some servers recompress and break text.
- [ ] Set a calendar reminder for one month: check citations, check that the
      record has not been duplicated.

---

## 7. Metadata checklist (copy this into every form)

Use these strings verbatim. Consistency is what disambiguates records.

- **Title:** `The Half-Life of Peace: Multilingual Measurement of Public Attention Decay After Ceasefires, 2015-2025`
- **Author (one form, everywhere):** `Ahmed Jaffar`
- **Affiliation:** `Independent researcher` (or your real institution, spelled consistently)
- **Date:** `2026-11-07` in ISO form on repository forms; `7 November 2026` on the PDF cover
- **Type:** Preprint
- **License:** CC BY 4.0 (paper and data); MIT (code)
- **Keywords (6-10):** ceasefire durability; attention decay; issue-attention cycle; Wikipedia pageviews; conflict early warning; peace agreements; computational social science; multilingual measurement
- **JEL codes (SSRN/SocArXiv):** D74, D83, F51
- **arXiv categories:** cs.SI (primary), econ.GN (cross-list)
- **Abstract (250 words):** as in the manuscript
- **Short abstract (60 words):** `Attention to ceasefires fades at a measurable rate. Using daily Wikipedia pageviews in 14 languages alongside 40 verified ceasefires from 2015-2025 and UCDP fatality data, we estimate the Peace Attention Half-Life, test it against placebo dates, and ask whether slower decay predicts ceasefire survival.`
- **DOI:** Zenodo version DOI for the paper record; concept DOI in the README
- **Repository:** `https://github.com/AhmedJaffar/half-life-of-peace`
- **PDF filename:** `Jaffar_2026_Half-Life-of-Peace.pdf`

A note on the 60-word abstract: update it once the results are final so that the
one sentence a journalist would quote carries the actual headline estimate.
Never ship a short abstract containing numbers that the paper does not contain.

---

## 8. What a preprint does and does not do

**It does:** establish priority and a timestamp; make the work citable before
peer review; give you a DOI and a permanent link you can put on a CV; invite
substantive criticism; and make the work readable by people without journal
access, which for a paper about global attention to conflict is not a small
thing.

**It does not:** confer peer review, improve the paper's correctness, or
guarantee credibility with a sceptical reader. A preprint by an independent
researcher with a small exploratory sample will be read as exactly what it is,
and the manuscript should say so plainly - which it does. It also does not
guarantee Google Scholar inclusion, citation, or attention. Most preprints are
read by very few people. The realistic outcome to aim for is that the twenty
people who care about ceasefire durability and computational measurement find
it, that two or three cite or critique it, and that the dataset is reused.

One more thing worth stating: do not chase indexing as an end in itself. The
durable way to be found is to have a measurement someone needs, a reproducible
dataset, and a clear statement of what is and is not established. The
infrastructure above exists to make sure that when someone searches for it,
they can find it.
