"""Download and aggregate UCDP Georeferenced Event Dataset (GED).

Version strategy (reproducible)
-------------------------------
``GED_VERSION = "26.1"`` (GED 26.1, released 2026-03-30) is the primary release:
it covers events through 2025-12, which the project needs for 12-month
fatality follow-up on ceasefires up to Gaza (2025-01) and India-Pakistan
(2025-05).  ``FALLBACK_VERSION = "24.1"`` (2024-05-22) is used only if the
primary release cannot be downloaded or parsed.  The version actually used is
recorded in ``data/raw/ucdp/ucdp_summary.json`` and in ``data/README.md``.

Source
------
https://ucdp.uu.se/downloads/ged/ged261-csv.zip
The UCDP API returns HTTP 401, so the official static zip is used.

What this script does
---------------------
1. Download the zip once to ``data/raw/ucdp/`` (cached; a re-run is offline),
   verify it is a valid zip, and extract the event CSV.
2. Parse the event table in chunks with pandas, keep events with
   ``year >= 2014``, derive the event month from ``date_start``.
3. Aggregate the UCDP *best* fatality estimate to monthly totals:
   * by event country, mapped to ISO-3166 alpha-3
     -> ``data/processed/ucdp_monthly_country.csv`` (iso3, month, fatalities, events)
   * by dyad -> ``data/processed/ucdp_monthly_dyad.csv``
       (dyad_new_id, dyad_name, month, fatalities, events)
4. Write ``data/processed/ucdp_country_mapping.csv``: an explicit
   theatre-ISO3 -> UCDP-country-label crosswalk so downstream joins never have
   to guess.  GED's ``country`` field is the *location* of the event, so Gaza
   events are coded ``Israel``; there is no ``PSE`` series in GED.  Non-identity
   rows (label aliases and the PSE->Israel proxy) are documented in README.
"""
from __future__ import annotations

import csv
import json
import sys
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

try:  # normal package import (run_all / python -m src.ucdp)
    from .common import DATA_PROCESSED, DATA_RAW, USER_AGENT, ensure_dirs, log
except ImportError:  # pragma: no cover - direct `python src/ucdp.py`
    sys.path[:] = [p for p in sys.path if p != str(Path(__file__).resolve().parent)]
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from src.common import DATA_PROCESSED, DATA_RAW, USER_AGENT, ensure_dirs, log  # type: ignore

GED_VERSION = "26.1"
FALLBACK_VERSION = "24.1"
GED_URL_TEMPLATE = "https://ucdp.uu.se/downloads/ged/ged{slug}-csv.zip"
MIN_YEAR = 2014

# GED country label -> ISO3.  Covers every country label in GED 24.1/26.1 for
# events with year >= 2014 (101 countries in 26.1).
ISO3 = {
    "Afghanistan": "AFG",
    "Algeria": "DZA",
    "Angola": "AGO",
    "Argentina": "ARG",
    "Armenia": "ARM",
    "Australia": "AUS",
    "Austria": "AUT",
    "Azerbaijan": "AZE",
    "Bangladesh": "BGD",
    "Belgium": "BEL",
    "Benin": "BEN",
    "Bolivia": "BOL",
    "Brazil": "BRA",
    "Burkina Faso": "BFA",
    "Burundi": "BDI",
    "Cambodia (Kampuchea)": "KHM",
    "Cameroon": "CMR",
    "Central African Republic": "CAF",
    "Chad": "TCD",
    "China": "CHN",
    "Colombia": "COL",
    "Congo": "COG",
    "Costa Rica": "CRI",
    "DR Congo (Zaire)": "COD",
    "Djibouti": "DJI",
    "Ecuador": "ECU",
    "Egypt": "EGY",
    "El Salvador": "SLV",
    "Eritrea": "ERI",
    "Ethiopia": "ETH",
    "France": "FRA",
    "Gambia": "GMB",
    "Georgia": "GEO",
    "Germany": "DEU",
    "Ghana": "GHA",
    "Guatemala": "GTM",
    "Guinea": "GIN",
    "Haiti": "HTI",
    "Honduras": "HND",
    "India": "IND",
    "Indonesia": "IDN",
    "Iran": "IRN",
    "Iraq": "IRQ",
    "Israel": "ISR",
    "Ivory Coast": "CIV",
    "Jamaica": "JAM",
    "Jordan": "JOR",
    "Kenya": "KEN",
    "Kingdom of eSwatini (Swaziland)": "SWZ",
    "Kuwait": "KWT",
    "Kyrgyzstan": "KGZ",
    "Lebanon": "LBN",
    "Liberia": "LBR",
    "Libya": "LBY",
    "Madagascar (Malagasy)": "MDG",
    "Malaysia": "MYS",
    "Mali": "MLI",
    "Malta": "MLT",
    "Mauritania": "MRT",
    "Mexico": "MEX",
    "Morocco": "MAR",
    "Mozambique": "MOZ",
    "Myanmar (Burma)": "MMR",
    "Nepal": "NPL",
    "Netherlands": "NLD",
    "Niger": "NER",
    "Nigeria": "NGA",
    "Pakistan": "PAK",
    "Papua New Guinea": "PNG",
    "Paraguay": "PRY",
    "Peru": "PER",
    "Philippines": "PHL",
    "Poland": "POL",
    "Qatar": "QAT",
    "Russia (Soviet Union)": "RUS",
    "Rwanda": "RWA",
    "Saudi Arabia": "SAU",
    "Senegal": "SEN",
    "Sierra Leone": "SLE",
    "Somalia": "SOM",
    "South Africa": "ZAF",
    "South Sudan": "SSD",
    "Spain": "ESP",
    "Sri Lanka": "LKA",
    "Sudan": "SDN",
    "Sweden": "SWE",
    "Syria": "SYR",
    "Tajikistan": "TJK",
    "Tanzania": "TZA",
    "Thailand": "THA",
    "Togo": "TGO",
    "Tunisia": "TUN",
    "Turkey": "TUR",
    "Uganda": "UGA",
    "Ukraine": "UKR",
    "United Arab Emirates": "ARE",
    "United Kingdom": "GBR",
    "United States of America": "USA",
    "Venezuela": "VEN",
    "Yemen (North Yemen)": "YEM",
    "Zimbabwe (Rhodesia)": "ZWE",
}

# GED labels whose text is not the plain ISO-3166 short name.
LABEL_ALIASES = {
    "COD",
    "SWZ",
    "MMR",
    "RUS",
    "YEM",
    "KHM",
    "MDG",
    "CIV",
    "COG",
    "USA",
    "GBR",
    "ARE",
}

# Theatre ISO3 -> UCDP country label where a non-identity join is required.
# GED country is the event LOCATION, so Gaza/West Bank events are coded Israel.
NON_IDENTITY_MAPPINGS = {
    "PSE": {
        "ucdp_country": "Israel",
        "mapping_type": "proxy",
        "note": (
            "GED codes the event-location country; events in Gaza and the West Bank "
            "appear under Israel. GED has no PSE rows, so join Gaza/PSE ceasefires "
            "to Israeli fatalities."
        ),
    },
}

USECOLS = [
    "id",
    "year",
    "type_of_violence",
    "conflict_name",
    "dyad_new_id",
    "dyad_name",
    "country",
    "country_id",
    "region",
    "date_start",
    "best",
]


# ---------------------------------------------------------------------------
# version / path helpers
# ---------------------------------------------------------------------------
def version_slug(version: str) -> str:
    return version.replace(".", "")


def ged_url(version: str) -> str:
    return GED_URL_TEMPLATE.format(slug=version_slug(version))


def ged_zip_path(version: str) -> Path:
    return DATA_RAW / "ucdp" / "ged{}-csv.zip".format(version_slug(version))


def ged_csv_path(version: str) -> Path:
    return DATA_RAW / "ucdp" / "GEDEvent_v{}.csv".format(version.replace(".", "_"))


# ---------------------------------------------------------------------------
# download / extract
# ---------------------------------------------------------------------------
def _valid_zip(path: Path) -> bool:
    try:
        with zipfile.ZipFile(path) as zf:
            return zf.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def download_ged(version: str = GED_VERSION, refresh: bool = False) -> Path:
    """Download the requested GED release and extract its CSV (idempotent)."""
    ensure_dirs(DATA_RAW / "ucdp")
    zip_path = ged_zip_path(version)
    csv_path = ged_csv_path(version)
    url = ged_url(version)

    need_download = refresh or not zip_path.exists() or not _valid_zip(zip_path)
    if need_download:
        log("ucdp: downloading GED {} (~40 MB) from {}".format(version, url))
        tmp = zip_path.with_suffix(".zip.part")
        last_exc = None
        for attempt in range(5):
            try:
                with requests.get(
                    url, stream=True, timeout=300, headers={"User-Agent": USER_AGENT}
                ) as resp:
                    resp.raise_for_status()
                    written = 0
                    with open(tmp, "wb") as fh:
                        for chunk in resp.iter_content(chunk_size=1024 * 1024):
                            if chunk:
                                fh.write(chunk)
                                written += len(chunk)
                if written < 10 * 1024 * 1024:
                    raise RuntimeError("download too small ({} bytes)".format(written))
                if not _valid_zip(tmp):
                    raise RuntimeError("downloaded zip failed integrity test")
                tmp.replace(zip_path)
                log("ucdp: downloaded GED {} ({:,} bytes)".format(version, written))
                last_exc = None
                break
            except Exception as exc:  # noqa: BLE001 - retry any transport/zip failure
                last_exc = exc
                log("ucdp: download attempt {} for GED {} failed: {}".format(attempt + 1, version, exc))
                time.sleep(min(2 ** attempt, 30))
        if last_exc is not None:
            raise RuntimeError("could not download GED {}: {}".format(version, last_exc))
    else:
        log("ucdp: using cached GED {} zip {}".format(version, zip_path))

    if not csv_path.exists():
        log("ucdp: extracting {} from GED {}".format(csv_path.name, version))
        with zipfile.ZipFile(zip_path) as zf:
            members = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not members:
                raise RuntimeError("no CSV found inside GED zip: {}".format(zf.namelist()))
            member = members[0]
            info = zf.getinfo(member)
            with zf.open(member) as src, open(csv_path, "wb") as dst:
                while True:
                    block = src.read(4 * 1024 * 1024)
                    if not block:
                        break
                    dst.write(block)
        log(
            "ucdp: extracted {} ({:,} bytes)".format(
                member, csv_path.stat().st_size
            )
        )
    return csv_path


# ---------------------------------------------------------------------------
# country mapping
# ---------------------------------------------------------------------------
def write_country_mapping(observed_country_ids):
    """Write the theatre-ISO3 -> UCDP-country crosswalk."""
    rows = []
    for ged_label, iso3 in sorted(ISO3.items(), key=lambda kv: kv[1]):
        if iso3 in NON_IDENTITY_MAPPINGS:
            continue
        rows.append(
            {
                "theatre_iso3": iso3,
                "ucdp_country": ged_label,
                "ucdp_country_id": observed_country_ids.get(ged_label, ""),
                "mapping_type": "alias" if iso3 in LABEL_ALIASES else "identity",
                "note": "",
            }
        )
    for iso3, spec in NON_IDENTITY_MAPPINGS.items():
        rows.append(
            {
                "theatre_iso3": iso3,
                "ucdp_country": spec["ucdp_country"],
                "ucdp_country_id": observed_country_ids.get(spec["ucdp_country"], ""),
                "mapping_type": spec["mapping_type"],
                "note": spec["note"],
            }
        )
    rows.sort(key=lambda r: r["theatre_iso3"])
    path = DATA_PROCESSED / "ucdp_country_mapping.csv"
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "theatre_iso3",
                "ucdp_country",
                "ucdp_country_id",
                "mapping_type",
                "note",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
    log("ucdp: country mapping ({} rows) -> {}".format(len(rows), path))
    return path


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------
def aggregate(csv_path: Path, version: str = GED_VERSION):
    """Aggregate GED events year>=2014 to monthly fatalities/events."""
    ensure_dirs(DATA_PROCESSED)

    country_frames = []
    dyad_frames = []
    total_parsed = 0
    kept = 0
    dropped_bad_date = 0
    unmapped = {}
    observed_country_ids = {}

    reader = pd.read_csv(
        csv_path,
        usecols=USECOLS,
        dtype=str,
        chunksize=100_000,
        low_memory=False,
    )
    for chunk in reader:
        total_parsed += len(chunk)
        chunk["year_int"] = pd.to_numeric(chunk["year"], errors="coerce")
        chunk = chunk[chunk["year_int"] >= MIN_YEAR].copy()
        if chunk.empty:
            continue
        kept += len(chunk)
        for label, cid in zip(chunk["country"], chunk["country_id"]):
            if label and label not in observed_country_ids and cid:
                observed_country_ids[label] = cid
        chunk["month"] = pd.to_datetime(chunk["date_start"], errors="coerce").dt.strftime("%Y-%m")
        bad = chunk["month"].isna()
        dropped_bad_date += int(bad.sum())
        chunk = chunk[~bad].copy()
        if chunk.empty:
            continue

        chunk["fatalities"] = (
            pd.to_numeric(chunk["best"], errors="coerce").fillna(0).astype("int64")
        )
        chunk["iso3"] = chunk["country"].map(ISO3)
        for name in chunk.loc[chunk["iso3"].isna(), "country"].dropna().unique():
            unmapped[name] = unmapped.get(name, 0) + 1

        country_frames.append(
            chunk.dropna(subset=["iso3"])
            .groupby(["iso3", "month"], as_index=False)
            .agg(fatalities=("fatalities", "sum"), events=("fatalities", "size"))
        )
        dyad_frames.append(
            chunk.dropna(subset=["dyad_name"])
            .groupby(["dyad_new_id", "dyad_name", "month"], as_index=False)
            .agg(fatalities=("fatalities", "sum"), events=("fatalities", "size"))
        )

    country_monthly = (
        pd.concat(country_frames, ignore_index=True)
        .groupby(["iso3", "month"], as_index=False)
        .agg(fatalities=("fatalities", "sum"), events=("events", "sum"))
        .sort_values(["iso3", "month"])
    )
    dyad_monthly = (
        pd.concat(dyad_frames, ignore_index=True)
        .groupby(["dyad_new_id", "dyad_name", "month"], as_index=False)
        .agg(fatalities=("fatalities", "sum"), events=("events", "sum"))
        .sort_values(["dyad_new_id", "month"])
    )

    country_path = DATA_PROCESSED / "ucdp_monthly_country.csv"
    dyad_path = DATA_PROCESSED / "ucdp_monthly_dyad.csv"
    country_monthly.to_csv(country_path, index=False)
    dyad_monthly.to_csv(dyad_path, index=False)
    mapping_path = write_country_mapping(observed_country_ids)

    zip_info = {}
    try:
        with zipfile.ZipFile(ged_zip_path(version)) as zf:
            member = [n for n in zf.namelist() if n.lower().endswith(".csv")][0]
            info = zf.getinfo(member)
            zip_info = {
                "member": member,
                "member_mtime": "{:04d}-{:02d}-{:02d}".format(*info.date_time[:3]),
                "zip_bytes": ged_zip_path(version).stat().st_size,
            }
    except Exception:  # noqa: BLE001 - summary is best-effort metadata
        zip_info = {}

    summary = {
        "source": ged_url(version),
        "version": "GED v{}".format(version),
        "retrieval_date": "2026-11-07",
        "zip_info": zip_info,
        "events_parsed_total": int(total_parsed),
        "events_year_ge_2014": int(kept),
        "events_dropped_bad_date": int(dropped_bad_date),
        "country_rows": int(len(country_monthly)),
        "dyad_rows": int(len(dyad_monthly)),
        "countries_covered": int(country_monthly["iso3"].nunique()),
        "dyads_covered": int(dyad_monthly["dyad_name"].nunique()),
        "month_min": str(country_monthly["month"].min()),
        "month_max": str(country_monthly["month"].max()),
        "total_fatalities_best": int(country_monthly["fatalities"].sum()),
        "total_events": int(country_monthly["events"].sum()),
        "unmapped_countries": unmapped,
        "country_mapping_file": str(mapping_path.relative_to(DATA_RAW.parents[0])),
    }
    summary_path = DATA_RAW / "ucdp" / "ucdp_summary.json"
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)

    log(
        "ucdp: GED v{} -> {:,} events parsed, {:,} kept (year>={}), {:,} bad dates; "
        "{} country-months ({} countries), {} dyad-months ({} dyads), months {}..{}; "
        "{:,} fatalities, {:,} events".format(
            version,
            total_parsed,
            kept,
            MIN_YEAR,
            dropped_bad_date,
            len(country_monthly),
            summary["countries_covered"],
            len(dyad_monthly),
            summary["dyads_covered"],
            summary["month_min"],
            summary["month_max"],
            summary["total_fatalities_best"],
            summary["total_events"],
        )
    )
    if unmapped:
        log("ucdp: WARNING unmapped country labels (not written to country table): {}".format(unmapped))
    return summary


def run(refresh: bool = False, version: str = None):
    """Download + aggregate the primary GED release, falling back to v24.1."""
    versions = [version] if version else [GED_VERSION, FALLBACK_VERSION]
    last_error = None
    for candidate in versions:
        try:
            csv_path = download_ged(candidate, refresh=refresh)
            return aggregate(csv_path, candidate)
        except Exception as exc:  # noqa: BLE001 - try the fallback release
            last_error = exc
            log("ucdp: GED v{} failed ({}); trying fallback".format(candidate, exc))
    raise RuntimeError("could not build UCDP aggregates: {}".format(last_error))


def main(argv=None):
    import argparse

    parser = argparse.ArgumentParser(description="Build UCDP GED monthly aggregates")
    parser.add_argument("--refresh", action="store_true", help="re-download the zip")
    parser.add_argument(
        "--version",
        default=None,
        help="GED version, e.g. 26.1 (default: primary, then fallback)",
    )
    args = parser.parse_args(argv)
    run(refresh=args.refresh, version=args.version)


if __name__ == "__main__":  # pragma: no cover
    main()
