"""Configuration for the statistical analysis stage.

Lives outside ``src/`` so that the measurement code stays free of
study-design choices.  All defaults here are decisions of the analysis plan in
``task-3`` and are documented in ``analysis/report.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # allow `python analysis/run.py`
    sys.path.insert(0, str(PROJECT_ROOT))

DATA = PROJECT_ROOT / "data"
PROCESSED = DATA / "processed"
EVENTS = DATA / "events"
ANALYSIS_DIR = PROJECT_ROOT / "analysis"
TABLES_DIR = ANALYSIS_DIR / "tables"
FIGURES_DIR = PROJECT_ROOT / "figures"

# --- inputs (read at runtime; never cached into code) ----------------------
PAGEVIEWS = PROCESSED / "pageviews.csv"
ARTICLES = PROCESSED / "articles.csv"
LANGLINKS = PROCESSED / "article_langlinks.csv"
UCDP_COUNTRY = PROCESSED / "ucdp_monthly_country.csv"
UCDP_DYAD = PROCESSED / "ucdp_monthly_dyad.csv"
UCDP_MAPPING = PROCESSED / "ucdp_country_mapping.csv"
CEASEFIRES = EVENTS / "ceasefires.csv"

RESULTS_JSON = ANALYSIS_DIR / "results.json"
REPORT_MD = ANALYSIS_DIR / "report.md"
MANIFEST_JSON = ANALYSIS_DIR / "manifest.json"

# --- study design ----------------------------------------------------------
from src import config as _src_config  # noqa: E402

LANGS = list(_src_config.LANGS)              # 14 language editions
WAR_CONCEPTS = list(_src_config.WAR_CONCEPTS)
PEACE_CONCEPTS = list(_src_config.PEACE_CONCEPTS)
STUDY_START = "2015-07-01"
STUDY_END = "2025-11-01"

# PAHL
PAHL_PRIMARY_WINDOW = 90                    # days after peak in the primary fit
PAHL_WINDOWS = (30, 90, 270)                # decay-window sensitivity
PAHL_MIN_LANGUAGES = 1                      # per-event fit needs >=1 language edition
PAHL_MULTILINGUAL_MIN = 2                   # 'multilingual only' robustness subset
PAHL_BOOT = 2000                            # cluster bootstrap for medians
EVENT_STUDY_TMIN = -90
EVENT_STUDY_TMAX = 365

# WPAR
WPAR_HAC_LAGS = 12

# resumption coding
RESUMPTION_THRESHOLD = 0.25
RESUMPTION_PRE_MONTHS = 6
RESUMPTION_SUSTAIN = 2
RESUMPTION_HORIZON = 12
THRESHOLD_SENSITIVITY = (0.10, 0.25, 0.50)

# prediction (exploratory: n is small)
RIDGE_PENALTY = 1.0
CV_FOLDS = 5
CV_REPEATS = 200
N_PERM = 1000
PLACEBO_PER_EVENT = 500
PLACEBO_STUDIES = 500
SEED = 20261107

# broad region label used when an event cannot be mapped to an article
REGION_BY_ISO3 = {
    "UKR": "Europe", "RUS": "Europe",
    "SYR": "Middle East", "YEM": "Middle East", "PSE": "Middle East",
    "ISR": "Middle East", "LBN": "Middle East", "IRN": "Middle East",
    "AFG": "Asia", "PAK": "Asia", "THA": "Asia", "MMR": "Asia",
    "PHL": "Asia", "IND": "Asia",
    "MLI": "Africa", "SSD": "Africa", "SDN": "Africa", "CAF": "Africa",
    "COD": "Africa", "ETH": "Africa", "LBY": "Africa",
    "COL": "Americas", "AZE": "Caucasus",
}
