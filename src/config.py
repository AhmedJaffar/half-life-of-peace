"""Central configuration for *The Half-Life of Peace*.

Every downstream module imports its constants from here so that the study
window, language set, and concept baskets are defined exactly once.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "raw"
ANALYSIS = ROOT / "analysis"
FIGURES = ROOT / "figures"

# --- Language editions -------------------------------------------------------
# Chosen to span the theatres of the covered conflicts plus the major
# mediator / donor states.  English included for reference.
LANGS = ["en", "ar", "es", "fr", "de", "ru", "zh", "fa", "tr", "id", "pt", "uk", "he", "hi"]
CONCEPT_LANGS = LANGS  # concept pages exist in all of these (verified)

# --- Concept families --------------------------------------------------------
# WAR and PEACE baskets of comparable size so that the War-Peace Attention
# Ratio is not mechanically driven by basket length.
WAR_CONCEPTS = [
    "War",
    "Armed conflict",
    "Civil war",
    "Invasion",
    "Airstrike",
    "Genocide",
    "Terrorism",
    "Military occupation",
    "Refugee",
    "War crime",
]

PEACE_CONCEPTS = [
    "Peace",
    "Ceasefire",
    "Peace treaty",
    "Peacebuilding",
    "Mediation",
    "Diplomacy",
    "Reconciliation (theology)",
    "Disarmament",
    "Demobilization",
    "Peacekeeping",
    "Humanitarian aid",
]

# --- Study window ------------------------------------------------------------
# Wikimedia pageview data begins 2015-07-01; the per-article REST endpoint for
# this project returns daily data through 2025-11-01 (verified).
DATE_START = "20150701"
DATE_END = "20251101"

# --- Event-analysis windows (days) ------------------------------------------
PRE_BASELINE_START = -90   # baseline window starts here relative to t0
PRE_BASELINE_END = -30     # ... and ends here (skip any announcement run-up)
PEAK_WINDOW_END = 14       # peak is searched in [t0, t0 + 14]
MAX_FOLLOWUP = 180         # censoring horizon for half-life estimation
SMOOTH_WINDOW = 7          # centred rolling median for decay curves

# --- HTTP --------------------------------------------------------------------
USER_AGENT = (
    "HalfLifeOfPeace/0.1 (https://github.com/AhmedJaffar/half-life-of-peace; "
    "research; contact: ahmedjaffar.ca)"
)
API_SLEEP = 0.05
MAX_WORKERS = 5
