"""Sidebar filters + split-membership filtering of semicolon-separated fields."""
from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd
import streamlit as st

from .data import ordered_counts

DEFAULT_INT = (0, 11)


@dataclass
class FilterState:
    years: tuple[int, int]
    include_undated: bool
    countries: list[str] = field(default_factory=list)
    types: list[str] = field(default_factory=list)
    sectors: list[str] = field(default_factory=list)
    intensity: tuple[int, int] = DEFAULT_INT
    full_years: tuple[int, int] = (2000, 2024)

    def is_active(self) -> bool:
        return bool(
            self.countries or self.types or self.sectors
            or self.years != self.full_years or self.intensity != DEFAULT_INT
        )

    def summary(self) -> list[str]:
        out = []
        if self.years != self.full_years:
            out.append(f"years {self.years[0]}–{self.years[1]}")
        if self.countries:
            out.append(f"{len(self.countries)} countr{'y' if len(self.countries) == 1 else 'ies'}")
        if self.types:
            out.append(f"{len(self.types)} attack type(s)")
        if self.sectors:
            out.append(f"{len(self.sectors)} sector(s)")
        if self.intensity != DEFAULT_INT:
            out.append(f"intensity {self.intensity[0]}–{self.intensity[1]}")
        return out


def _reset(year_min: int, year_max: int) -> None:
    st.session_state["f_years"] = (year_min, year_max)
    st.session_state["f_undated"] = True
    st.session_state["f_countries"] = []
    st.session_state["f_types"] = []
    st.session_state["f_sectors"] = []
    st.session_state["f_int"] = DEFAULT_INT


def render_sidebar(df: pd.DataFrame) -> FilterState:
    y0, y1 = int(df["year"].min()), int(df["year"].max())
    w_min, w_max = int(df["weighted_intensity"].min()), int(df["weighted_intensity"].max())
    with st.sidebar:
        st.markdown("### 🛰️ CYBERPULSE")
        st.caption(
            "**EuRepoC Global Cyber Incidents v1.3** — a curated, historical repository of documented "
            "cyber incidents. It is *not* a real-time feed, and counts show what was documented, "
            "not total cyber activity."
        )
        st.divider()
        st.markdown("#### Filters")
        years = st.slider("Start year", y0, y1, (y0, y1), key="f_years")
        undated = st.checkbox(
            "Include incidents with unknown start date", value=True, key="f_undated",
            help="92 incidents have no usable start date. They can't be placed in a year, "
                 "so untick to see only dated incidents.",
        )
        countries = st.multiselect(
            "Target country / territory", list(ordered_counts(df, "countries").index), key="f_countries",
            placeholder="All countries (leave empty)",
            help="Matches incidents whose receiver list contains any selected country "
                 "(split membership, not text search). Incidents with no valid country are excluded when this is used.",
        )
        types = st.multiselect(
            "Attack type", list(ordered_counts(df, "types").index), key="f_types",
            placeholder="All attack types (leave empty)",
            help="An incident can have several attack types; it matches if it has any selected one.",
        )
        sectors = st.multiselect(
            "Target sector", list(ordered_counts(df, "sectors").index), key="f_sectors",
            placeholder="All sectors (leave empty)",
            help="An incident can target several sectors; it matches if it has any selected one.",
        )
        intensity = st.slider(
            "Weighted intensity", w_min, w_max, (w_min, w_max), key="f_int",
            help="Dataset-specific intensity score (EuRepoC). It is not a financial-loss metric.",
        )
        st.button("↺ Reset all filters", on_click=_reset, args=(y0, y1), use_container_width=True)
        st.divider()
        st.caption(
            "Multi-value fields are split on “;”. Category totals can exceed the number of incidents "
            "because one incident may belong to several categories."
        )
    return FilterState(
        years=(int(years[0]), int(years[1])), include_undated=undated, countries=countries,
        types=types, sectors=sectors, intensity=(int(intensity[0]), int(intensity[1])),
        full_years=(y0, y1),
    )


def apply_filters(df: pd.DataFrame, fs: FilterState) -> pd.DataFrame:
    in_range = df["year"].between(fs.years[0], fs.years[1])
    if fs.include_undated:
        in_range = in_range | df["year"].isna()
    mask = in_range & df["weighted_intensity"].between(*fs.intensity)
    for key, selected in (("countries", fs.countries), ("types", fs.types), ("sectors", fs.sectors)):
        if selected:
            wanted = set(selected)
            mask &= df[f"_{key}"].map(lambda items, w=wanted: not w.isdisjoint(items))
    return df[mask]
