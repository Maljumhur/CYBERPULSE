"""Data loading, parsing and multi-value helpers for CYBERPULSE.

Everything here operates on the *real* cleaned EuRepoC export. Nothing is simulated,
imputed or re-estimated: missing values stay missing.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent.parent / "eurepoc_cleaned.csv"

# multi-value (semicolon separated) analysis fields -> source column in the cleaned CSV
MULTI = {
    "types": "incident_type_clean",
    "sectors": "receiver_category_clean",
    "countries": "receiver_country_valid",
}

# first column added by the cleaning notebook; everything before it is the raw EuRepoC export
FIRST_CLEAN_COL = "incident_type_clean"

# ISO-3 codes for the globe (Plotly choropleth). Territories are kept as territories.
ISO3 = {
    "United States": "USA", "Russia": "RUS", "Germany": "DEU", "United Kingdom": "GBR", "Israel": "ISR",
    "France": "FRA", "Ukraine": "UKR", "India": "IND", "Korea, Republic of": "KOR", "Canada": "CAN",
    "China": "CHN", "Turkey": "TUR", "Japan": "JPN", "Italy": "ITA", "Iran, Islamic Republic of": "IRN",
    "Pakistan": "PAK", "Australia": "AUS", "Taiwan": "TWN", "Spain": "ESP", "Philippines": "PHL",
    "Saudi Arabia": "SAU", "Belgium": "BEL", "Mexico": "MEX", "Switzerland": "CHE",
    "United Arab Emirates": "ARE", "Vietnam": "VNM", "Netherlands": "NLD", "Brazil": "BRA",
    "Hong Kong": "HKG", "Thailand": "THA", "Poland": "POL", "Afghanistan": "AFG", "Singapore": "SGP",
    "Egypt": "EGY", "Chile": "CHL", "Argentina": "ARG", "Sweden": "SWE", "Malaysia": "MYS",
    "Syria": "SYR", "Indonesia": "IDN", "South Africa": "ZAF", "Denmark": "DNK", "Austria": "AUT",
    "Belarus": "BLR", "Azerbaijan": "AZE", "Venezuela": "VEN", "Palestine": "PSE", "Cambodia": "KHM",
    "Georgia": "GEO", "Lebanon": "LBN", "Colombia": "COL", "Bangladesh": "BGD", "Czech Republic": "CZE",
    "Lithuania": "LTU", "Armenia": "ARM", "Norway": "NOR", "Kazakhstan": "KAZ", "Peru": "PER",
    "Finland": "FIN", "Hungary": "HUN", "Kuwait": "KWT", "Estonia": "EST", "Myanmar": "MMR",
    "Qatar": "QAT", "Jordan": "JOR", "Portugal": "PRT", "Greece": "GRC", "Yemen": "YEM",
    "Romania": "ROU", "Morocco": "MAR", "Iraq": "IRQ", "Bahrain": "BHR", "Uzbekistan": "UZB",
    "Kenya": "KEN", "Ecuador": "ECU", "Kyrgyzstan": "KGZ", "Mongolia": "MNG", "Slovakia": "SVK",
    "Serbia": "SRB", "New Zealand": "NZL", "Cyprus": "CYP", "Latvia": "LVA", "Bulgaria": "BGR",
    "Korea, Democratic People's Republic of": "PRK", "Sri Lanka": "LKA", "Croatia": "HRV",
    "Paraguay": "PRY", "Moldova, Republic of": "MDA", "Uruguay": "URY", "Nepal": "NPL", "Libya": "LBY",
    "Albania": "ALB", "Nigeria": "NGA", "Slovenia": "SVN", "Tajikistan": "TJK", "Oman": "OMN",
    "Puerto Rico": "PRI", "Guatemala": "GTM", "Luxembourg": "LUX", "Uganda": "UGA", "Zimbabwe": "ZWE",
    "Tunisia": "TUN", "Costa Rica": "CRI", "Turkmenistan": "TKM", "Angola": "AGO", "Laos": "LAO",
    "Dominican Republic": "DOM", "Algeria": "DZA", "Brunei": "BRN", "El Salvador": "SLV",
    "Ireland": "IRL", "Senegal": "SEN", "New Caledonia": "NCL", "Seychelles": "SYC", "Cuba": "CUB",
    "Iceland": "ISL", "Tanzania": "TZA", "Montenegro": "MNE", "Holy See (Vatican City State)": "VAT",
    "Bolivia": "BOL", "Guyana": "GUY", "Honduras": "HND", "Bosnia and Herzegovina": "BIH",
    "Maldives": "MDV", "Sudan": "SDN", "Congo, the Democratic Republic of the": "COD", "Gabon": "GAB",
    "Namibia": "NAM", "Macao": "MAC", "Liechtenstein": "LIE", "Rwanda": "RWA", "Djibouti": "DJI",
    "North Macedonia": "MKD", "Nicaragua": "NIC", "Cameroon": "CMR", "Togo": "TGO",
    "Burkina Faso": "BFA", "Ghana": "GHA", "Botswana": "BWA", "Panama": "PAN", "Ethiopia": "ETH",
    "Fiji": "FJI", "Réunion": "REU", "Virgin Islands, British": "VGB", "Kosovo": "XKX",
    "Dominica": "DMA", "Palau": "PLW", "Grenada": "GRD", "Malawi": "MWI", "Malta": "MLT",
    "Guinea": "GIN", "Trinidad and Tobago": "TTO", "Bermuda": "BMU", "Madagascar": "MDG",
    "French Guiana": "GUF", "St. Vincent and the Grenadines": "VCT", "Bhutan": "BTN",
    "Burundi": "BDI", "Guam": "GUM", "Martinique": "MTQ", "Tonga": "TON", "Guernsey": "GGY",
    "Nauru": "NRU", "Swaziland": "SWZ", "Anguilla": "AIA", "Bahamas": "BHS",
}

# Intensity components that make up the (unweighted) intensity score in the EuRepoC codebook.
COMPONENTS = {
    "data_theft": "Data theft",
    "disruption": "Disruption",
    "hijacking": "Hijacking",
    "physical_effects_spatial": "Physical effects (spatial)",
    "physical_effects_temporal": "Physical effects (temporal)",
}
_SCORE_RE = re.compile(r"scores?\s+(\d+)\s+point", re.I)


def split_multi(value) -> list[str]:
    """'A; B;C' -> ['A', 'B', 'C']. Missing -> []. Order preserved, duplicates removed."""
    if not isinstance(value, str):
        return []
    out: list[str] = []
    for part in value.split(";"):
        part = part.strip()
        if part and part not in out:
            out.append(part)
    return out


def component_score(text) -> float:
    """Points a component contributes, parsed from the codebook label.
    'none' -> 0, 'Not available' -> NaN (kept missing), '... scores N point(s)' -> N."""
    if not isinstance(text, str):
        return np.nan
    t = text.strip()
    if t.lower() == "none":
        return 0.0
    m = _SCORE_RE.search(t)
    if m:
        return float(m.group(1))
    return np.nan


@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, low_memory=False)
    for col in ("start_date_clean", "end_date_clean"):
        df[col] = pd.to_datetime(df[col], errors="coerce")
    df["year"] = df["start_date_clean"].dt.year  # float with NaN for unknown dates (kept missing)
    for key, col in MULTI.items():
        df[f"_{key}"] = df[col].map(split_multi)
    return df


def raw_columns(df: pd.DataFrame) -> list[str]:
    cols = [c for c in df.columns if not c.startswith("_") and c != "year"]
    return cols


def explode(df: pd.DataFrame, key: str, extra: tuple[str, ...] = ("weighted_intensity",)) -> pd.DataFrame:
    """One row per (incident, category value). Unique incident_id per value."""
    col = f"_{key}"
    out = (
        df[["incident_id", col, *extra]]
        .explode(col)
        .dropna(subset=[col])
        .rename(columns={col: "value"})
    )
    return out.drop_duplicates(["incident_id", "value"])


def ordered_counts(df: pd.DataFrame, key: str) -> pd.Series:
    """Unique-incident count per category, most frequent first."""
    return explode(df, key, extra=()).groupby("value")["incident_id"].nunique().sort_values(ascending=False)
