# Data and manuscript licence

**Manuscript** (`paper/`) and **derived datasets** (`data/processed/`, `data/events/`, `analysis/`, `figures/`):
© 2026 Ahmed Jaffar, licensed under
[Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/).

You are free to share and adapt this material for any purpose, provided you give appropriate credit,
link to the licence, and indicate whether changes were made.

**Code** (`src/`, `scripts/`, `analysis/*.py`): MIT — see [`LICENSE`](LICENSE).

## Upstream sources

This project redistributes derived aggregates, not raw upstream data. The underlying sources carry
their own terms, which govern reuse of the raw data:

| Source | Used for | Terms |
|---|---|---|
| [Wikimedia pageviews API](https://wikimedia.org/api/rest_v1/) | Attention measure | Wikimedia [Terms of Use](https://foundation.wikimedia.org/wiki/Policy:Terms_of_Use) and API [etiquette](https://www.mediawiki.org/wiki/API:Etiquette). Derived aggregates are released here under CC BY 4.0 with attribution to Wikimedia. |
| [UCDP Georeferenced Event Dataset](https://ucdp.uu.se/downloads/) v26.1 | Violence outcome | UCDP data are free to use with citation; see the UCDP [terms](https://ucdp.uu.se/downloads/). Cite Davies et al. (2024) as directed by UCDP. |

Raw downloads are **not** committed to this repository; `scripts/run_all.py` retrieves them.
