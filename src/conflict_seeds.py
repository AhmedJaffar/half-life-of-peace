"""Conflict-specific seed articles for the Half-Life of Peace project.

Thirty English Wikipedia articles covering the conflict theatres of the
2015-2025 ceasefire events (plus the main antecedents).  Each seed carries:

* ``conflict``      - the conflict label (joins to the curated ceasefire table)
* ``country_iso3``  - the primary theatre country (UCDP GED / ISO-3166 alpha-3)
* ``region``        - coarse region for descriptive tables

Concept baskets (WAR / PEACE) live in :mod:`src.config` (the project's single
source of truth); this module only adds the conflict-specific basket.
"""
from __future__ import annotations

# (article_en, conflict label, primary theatre ISO3, region)
CONFLICT_ARTICLES = [
    ("Russian invasion of Ukraine", "Russo-Ukrainian War", "UKR", "Europe"),
    ("War in Donbas", "Russo-Ukrainian War", "UKR", "Europe"),
    ("Syrian civil war", "Syrian civil war", "SYR", "Middle East"),
    ("Yemeni civil war (2014–present)", "Yemeni civil war", "YEM", "Middle East"),
    ("Tigray War", "Tigray War", "ETH", "Africa"),
    ("Gaza war", "Israeli–Palestinian conflict", "PSE", "Middle East"),
    ("Israel–Hezbollah conflict (2023–2024)", "Israel–Hezbollah conflict", "LBN", "Middle East"),
    ("Nagorno-Karabakh conflict", "Nagorno-Karabakh conflict", "AZE", "Caucasus"),
    ("Second Nagorno-Karabakh War", "Nagorno-Karabakh conflict", "AZE", "Caucasus"),
    ("War in Sudan (2023)", "Sudanese civil war (2023–present)", "SDN", "Africa"),
    ("War in Darfur", "Darfur conflict", "SDN", "Africa"),
    ("Libyan civil war (2014–2020)", "Libyan civil war", "LBY", "Africa"),
    ("Colombian conflict", "Colombian conflict", "COL", "Americas"),
    ("War in Afghanistan (2001–2021)", "War in Afghanistan", "AFG", "Asia"),
    ("Myanmar civil war (2021–present)", "Myanmar civil war", "MMR", "Asia"),
    ("South Sudanese Civil War", "South Sudanese Civil War", "SSD", "Africa"),
    ("Iraq War", "Iraq War", "IRQ", "Middle East"),
    ("War in Iraq (2013–2017)", "War in Iraq (2013–2017)", "IRQ", "Middle East"),
    ("Somali Civil War", "Somali Civil War", "SOM", "Africa"),
    ("Boko Haram insurgency", "Boko Haram insurgency", "NGA", "Africa"),
    ("Mali War", "Mali War", "MLI", "Africa"),
    ("Central African Republic Civil War", "Central African Republic Civil War", "CAF", "Africa"),
    ("Kivu conflict", "Kivu conflict", "COD", "Africa"),
    ("Insurgency in Khyber Pakhtunkhwa", "Insurgency in Khyber Pakhtunkhwa", "PAK", "Asia"),
    ("Kashmir conflict", "Kashmir conflict", "IND", "Asia"),
    ("Rohingya genocide", "Rohingya conflict", "MMR", "Asia"),
    ("Mexican drug war", "Mexican drug war", "MEX", "Americas"),
    ("Philippine drug war", "Philippine drug war", "PHL", "Asia"),
    ("Kurdish–Turkish conflict", "Kurdish–Turkish conflict", "TUR", "Middle East"),
    ("Insurgency in the Maghreb (2002–present)", "Insurgency in the Maghreb", "DZA", "Africa"),
]


def conflict_seed_rows():
    """One row per conflict-specific seed article."""
    return [
        {
            "seed_title": title,
            "family": "conflict",
            "concept": "",
            "conflict": conflict,
            "country_iso3": iso3,
            "region": region,
        }
        for title, conflict, iso3, region in CONFLICT_ARTICLES
    ]
