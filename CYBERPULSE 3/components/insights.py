"""Insight text. 'live' insights are computed from the filtered view; 'full' ones from the whole dataset."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .charts import category_stats
from .data import explode


def _small(n: int) -> str:
    return f" The current view holds only {n:,} incidents, so treat patterns as indicative." if n < 30 else ""


def _filter_note(active: bool, field: str) -> str:
    return (f" A filter on {field} is active, so bars show every {field} category found on the selected incidents."
            if active else "")


def category_insight(df, key, metric, label, filter_active=False, min_n=1):
    g = category_stats(df, key)
    N = df["incident_id"].nunique()
    if g.empty:
        return dict(what="No categories to summarise in this view.", why="", careful="", scope="live")
    if metric == "Frequency":
        g = g.sort_values("n", ascending=False)
        top = g.iloc[0]
        second = f"; next is {g.iloc[1]['value']} ({int(g.iloc[1]['n']):,})" if len(g) > 1 else ""
        what = (f"{top['value']} appears in {int(top['n']):,} of {N:,} incidents in view "
                f"({100 * top['n'] / N:.0f}%){second}.")
        why = f"Shows where documented {label} activity concentrates in the current selection."
        careful = ("Counts are documented incidents, not risk or prevalence. One incident can carry several "
                   f"{label} values, so bars add up to more than {N:,}." + _filter_note(filter_active, label) + _small(N))
    else:
        g = g[g["n"] >= min_n].sort_values(["median", "n"], ascending=False)
        if g.empty:
            return dict(what=f"No {label} has at least {min_n} incidents in this view.", why="", careful="", scope="live")
        hi, lo = g.iloc[0], g.iloc[-1]
        what = (f"Highest median weighted intensity: {hi['value']} ({hi['median']:g}, n={int(hi['n']):,}); "
                f"lowest shown: {lo['value']} ({lo['median']:g}, n={int(lo['n']):,}).")
        why = "Separates what is common from what is documented as more intense."
        careful = (f"Medians of integer scores tie often, and small groups are noisy (groups with n < {min_n} are hidden). "
                   "Intensity is a dataset-specific score, not financial loss." + _filter_note(filter_active, label))
    return dict(what=what, why=why, careful=careful, scope="live")


def year_insight(df, metric):
    d = df.dropna(subset=["year"])
    undated = int(df["year"].isna().sum())
    if d.empty:
        return dict(what="No incidents with a known start date in this view.", why="", careful="", scope="live")
    c = d.groupby("year")["incident_id"].nunique()
    peak = int(c.idxmax())
    if metric == "Frequency":
        what = f"Documented incidents peak in {peak} ({int(c.max()):,}) among incidents with a known start date."
    else:
        m = d.groupby("year")["weighted_intensity"].median()
        what = (f"Median weighted intensity ranges from {m.min():g} to {m.max():g} across years; "
                f"highest in {int(m.idxmax())}.")
    return dict(
        what=what,
        why="Shows when documentation clusters — useful context for any time-based comparison.",
        careful=("Counts depend on how thoroughly each period was documented and collected, so a rise is not proof of more "
                 f"attacks. {undated:,} incident(s) in view have no usable start date and are not plotted." + _small(len(d))),
        scope="live")


def country_insight(df, metric):
    return category_insight(df, "countries", metric, "country/territory", min_n=10 if metric != "Frequency" else 1) | dict(
        careful="Counts are not normalised by population, economy or size, and do not measure national risk — "
                "they reflect what was documented. Incidents without a valid country are not counted here.")


def hist_insight(df):
    vc = df["weighted_intensity"].value_counts()
    N = len(df)
    mode = int(vc.idxmax())
    low = int(df["weighted_intensity"].between(1, 4).sum())
    return dict(
        what=f"The most common weighted intensity is {mode} ({int(vc.max()):,} incidents); scores 1–4 cover {low:,} of {N:,} incidents ({100 * low / N:.0f}%).",
        why="Most documented incidents sit at the low-to-moderate end; high scores are rare, so extremes need context.",
        careful="Weighted intensity is an ordinal, dataset-specific score — not a measure of monetary or human cost." + _small(N),
        scope="live")


def box_insight(df):
    g = category_stats(df, "types")
    g = g[g["n"] >= 5].sort_values("median", ascending=False)
    if g.empty:
        return dict(what="Not enough incidents per attack type to compare.", why="", careful="", scope="live")
    hi, lo = g.iloc[0], g.iloc[-1]
    return dict(
        what=f"{hi['value']} has the highest median ({hi['median']:g}, n={int(hi['n']):,}); {lo['value']} the lowest ({lo['median']:g}, n={int(lo['n']):,}).",
        why="Compares how documented impact differs by method, not just how often each method appears.",
        careful="Incidents with several attack types appear in every matching box, so groups overlap. Integer scores make boxes collapse to lines; types with n < 5 are hidden.",
        scope="live")


def scatter_insight(df):
    n_diff = int((df["weighted_intensity"] != df["unweighted_intensity"]).sum())
    N = len(df)
    corr = df[["unweighted_intensity", "weighted_intensity"]].corr().iloc[0, 1] if N > 2 else np.nan
    c = f" Pearson correlation: {corr:.2f}." if not np.isnan(corr) else ""
    return dict(
        what=f"{n_diff:,} of {N:,} incidents have a weighted score different from their unweighted score.{c}",
        why="Shows how much the target-importance weighting changes the picture.",
        careful="Many incidents share the same pair of scores, so bubble size encodes the count. A strong correlation here is partly by construction of the score.",
        scope="live")


def heatmap_insight(df, min_n):
    a = explode(df, "sectors", extra=()).rename(columns={"value": "sector"})
    b = explode(df, "types", extra=()).rename(columns={"value": "type"})
    m = a.merge(b, on="incident_id").merge(df[["incident_id", "weighted_intensity"]], on="incident_id")
    g = m.groupby(["sector", "type"]).agg(n=("incident_id", "nunique"), med=("weighted_intensity", "median")).reset_index()
    g = g[g["n"] >= min_n].sort_values(["med", "n"], ascending=False)
    if g.empty:
        return dict(what=f"No sector × attack-type pair has at least {min_n} incidents in this view.", why="", careful="Lower the minimum sample size or widen the filters.", scope="live")
    r = g.iloc[0]
    return dict(
        what=f"Among pairs with n ≥ {min_n}, the highest median is {r['med']:g} for {r['sector']} × {r['type']} (n={int(r['n'])}). {len(g)} pairs qualify.",
        why="Highlights which target–method combinations carry more documented impact, not just more incidents.",
        careful="Cells with fewer incidents than the threshold are blank. Medians of small samples are fragile, and incidents with several sectors or types appear in several cells.",
        scope="live")


def map_insight(df, unmapped, n_missing):
    long = explode(df, "countries", extra=())
    c = long.groupby("value")["incident_id"].nunique().sort_values(ascending=False)
    if c.empty:
        return dict(what="No incidents with a valid target country in this view.", why="", careful="", scope="live")
    top = ", ".join(f"{k} ({v:,})" for k, v in c.head(3).items())
    return dict(
        what=f"Most documented incidents by target country: {top}. {len(c)} countries/territories appear in this view.",
        why="Gives a geographic feel for where incidents were documented.",
        careful=(f"Raw counts, not rates — larger or better-documented countries naturally show more. {n_missing:,} incident(s) in view have no valid country"
                 + (f"; {unmapped} small territory label(s) can't be drawn on the globe (see table)." if unmapped else ".")),
        scope="live")


def full_dataset_findings(df: pd.DataFrame) -> dict:
    """Notebook findings recomputed from the FULL cleaned file (never from filtered data)."""
    a = explode(df, "sectors").rename(columns={"value": "sector"})
    b = explode(df, "types", extra=()).rename(columns={"value": "type"})
    m = a.merge(b, on="incident_id")
    dis = m[m["type"] == "Disruption"].groupby("sector")["weighted_intensity"].median()
    hij = m[m["type"] == "Hijacking without Misuse"]["weighted_intensity"]
    tmed = m.groupby("type")["weighted_intensity"].median().sort_values(ascending=False)
    short = lambda s: s.split(" (")[0].split(" /")[0]
    return dict(
        disruption_ci=dis.get("Critical infrastructure"), disruption_edu=dis.get("Education"),
        disruption_state=dis.get("State institutions / political system"),
        hijack_share_1=float((hij == 1).mean()), top_type=tmed.index[0], top_type_median=float(tmed.iloc[0]),
        short=short,
    )
