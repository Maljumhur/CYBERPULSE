"""Plotly charts. Every builder returns (figure, table) or None when there is nothing to plot.
The table is the exact data behind the chart (shown in a 'View data' expander)."""
from __future__ import annotations

import textwrap

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .data import COMPONENTS, ISO3, component_score, explode

CYAN, BLUE, VIOLET, AMBER = "#20D9F3", "#3478F6", "#8265FF", "#FFC857"
BG, BG2, CARD = "#07111F", "#0D1B2A", "#12283D"
TEXT, MUTED = "#F2F7FF", "#91A6BE"
GRID = "rgba(145,166,190,0.14)"


def style(fig: go.Figure, height: int = 380, legend: bool = False) -> go.Figure:
    fig.update_layout(
        template=None, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=TEXT, size=13),
        margin=dict(l=8, r=12, t=12, b=8), height=height, showlegend=legend,
        hoverlabel=dict(bgcolor=CARD, bordercolor=CYAN, font=dict(color=TEXT, size=13)),
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED))
    return fig


def _short(s: str) -> str:
    """Display label without long parenthetical codebook notes (full text stays in hovers/tables)."""
    return s.split(" (")[0]


def _wrap(s: str, width: int = 26) -> str:
    s = _short(s)
    return "<br>".join(textwrap.wrap(s, width)) or s


# ---------------------------------------------------------------- category stats
def category_stats(df: pd.DataFrame, key: str) -> pd.DataFrame:
    long = explode(df, key)
    return (
        long.groupby("value")
        .agg(n=("incident_id", "nunique"), median=("weighted_intensity", "median"),
             mean=("weighted_intensity", "mean"))
        .reset_index()
    )


def category_bar(df: pd.DataFrame, key: str, metric: str = "Frequency", top_n: int = 10,
                 min_n: int = 1, height: int | None = None):
    g = category_stats(df, key)
    if g.empty:
        return None
    if metric == "Frequency":
        g = g.sort_values(["n", "value"], ascending=[False, True]).head(top_n)
        xs, text = g["n"], g["n"].map("{:,}".format)
        axis_title = "Unique incidents"
    else:
        g = g[g["n"] >= min_n].sort_values(["median", "n"], ascending=False).head(top_n)
        if g.empty:
            return None
        xs, text = g["median"], g.apply(lambda r: f"{r['median']:g}  (n={int(r['n']):,})", axis=1)
        axis_title = "Median weighted intensity"
    colors = [AMBER if i == 0 else CYAN for i in range(len(g))]
    fig = go.Figure(go.Bar(
        x=xs, y=g["value"].map(_wrap), orientation="h", marker_color=colors,
        marker_line_color=BG, marker_line_width=2, marker_cornerradius=4,
        text=text, textposition="outside", textfont=dict(color=TEXT), cliponaxis=False,
        customdata=np.stack([g["value"], g["n"], g["median"], g["mean"]], axis=-1),
        hovertemplate="<b>%{customdata[0]}</b><br>Unique incidents: %{customdata[1]:,}"
                      "<br>Median intensity: %{customdata[2]:g}<br>Mean intensity: %{customdata[3]:.2f}<extra></extra>",
    ))
    style(fig, height or max(300, 38 * len(g) + 60))
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=TEXT, size=12))
    fig.update_xaxes(title=axis_title, title_font=dict(color=MUTED), range=[0, float(xs.max()) * 1.28 + 1e-9])
    table = g.rename(columns={"value": "category", "n": "incidents"}).reset_index(drop=True)
    return fig, table


# ---------------------------------------------------------------- time
def year_chart(df: pd.DataFrame, metric: str = "Frequency"):
    d = df.dropna(subset=["year"])
    if d.empty:
        return None
    yrs = np.arange(int(d["year"].min()), int(d["year"].max()) + 1)
    g = d.groupby("year").agg(n=("incident_id", "nunique"), median=("weighted_intensity", "median")).reindex(yrs)
    g.index = g.index.astype(int)
    g["n"] = g["n"].fillna(0).astype(int)
    if metric == "Frequency":
        peak = g["n"].idxmax()
        fig = go.Figure(go.Bar(
            x=g.index, y=g["n"], marker_color=[AMBER if y == peak else CYAN for y in g.index],
            marker_line_color=BG, marker_line_width=2, marker_cornerradius=4,
            hovertemplate="<b>%{x}</b><br>Unique incidents: %{y:,}<extra></extra>",
        ))
        fig.update_yaxes(title="Unique incidents (by known start date)", title_font=dict(color=MUTED))
    else:
        gm = g.dropna(subset=["median"])
        fig = go.Figure(go.Scatter(
            x=gm.index, y=gm["median"], mode="lines+markers", line=dict(color=CYAN, width=2),
            marker=dict(size=9, color=CYAN, line=dict(color=BG, width=2)), customdata=gm["n"],
            hovertemplate="<b>%{x}</b><br>Median weighted intensity: %{y:g}<br>Incidents: %{customdata:,}<extra></extra>",
        ))
        fig.update_yaxes(title="Median weighted intensity", title_font=dict(color=MUTED))
    style(fig, 360)
    fig.update_xaxes(dtick=1 if len(yrs) <= 14 else None, tickangle=0 if len(yrs) <= 14 else -45)
    table = g.reset_index().rename(columns={"index": "year", "year": "year", "n": "incidents", "median": "median_weighted_intensity"})
    return fig, table


# ---------------------------------------------------------------- intensity
def intensity_hist(df: pd.DataFrame):
    if df.empty:
        return None
    vc = df["weighted_intensity"].value_counts()
    xs = np.arange(0, int(df["weighted_intensity"].max()) + 1)
    ys = vc.reindex(xs, fill_value=0)
    mode = int(vc.idxmax())
    fig = go.Figure(go.Bar(
        x=xs, y=ys.values, marker_color=[AMBER if x == mode else CYAN for x in xs],
        marker_line_color=BG, marker_line_width=2, marker_cornerradius=4,
        hovertemplate="Weighted intensity <b>%{x}</b><br>Incidents: %{y:,}<extra></extra>",
    ))
    style(fig, 340)
    fig.update_xaxes(title="Weighted intensity", dtick=1, title_font=dict(color=MUTED))
    fig.update_yaxes(title="Incidents", title_font=dict(color=MUTED))
    return fig, pd.DataFrame({"weighted_intensity": xs, "incidents": ys.values})


def type_box(df: pd.DataFrame, min_n: int = 5):
    long = explode(df, "types")
    if long.empty:
        return None
    stats = long.groupby("value").agg(n=("incident_id", "nunique"), median=("weighted_intensity", "median"))
    stats = stats[stats["n"] >= min_n].sort_values("median", ascending=False)
    if stats.empty:
        return None
    fig = go.Figure()
    for t, row in stats.iterrows():
        vals = long.loc[long["value"] == t, "weighted_intensity"]
        fig.add_trace(go.Box(
            x=vals, y=[f"{_wrap(t, 22)}<br><span style='color:{MUTED}'>n={int(row['n']):,}</span>"] * len(vals),
            orientation="h", name=t, marker_color=CYAN, line_color=CYAN, fillcolor="rgba(52,120,246,.35)",
            boxmean=True, boxpoints="outliers", marker_size=4,
            hovertemplate="<b>" + t + "</b><br>Weighted intensity: %{x}<extra></extra>",
        ))
    style(fig, max(320, 62 * len(stats) + 60))
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=TEXT, size=12))
    fig.update_xaxes(title="Weighted intensity (box = middle 50%, line = median, dashed = mean)", title_font=dict(color=MUTED))
    table = stats.reset_index().rename(columns={"value": "attack_type", "n": "incidents", "median": "median_weighted_intensity"})
    return fig, table


def scatter_bubble(df: pd.DataFrame):
    if df.empty:
        return None
    g = df.groupby(["unweighted_intensity", "weighted_intensity"]).size().reset_index(name="n")
    top = float(max(g["unweighted_intensity"].max(), g["weighted_intensity"].max()))
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[0, top], y=[0, top], mode="lines", line=dict(color=MUTED, width=1, dash="dot"),
        hoverinfo="skip", name="weighted = unweighted",
    ))
    fig.add_trace(go.Scatter(
        x=g["unweighted_intensity"], y=g["weighted_intensity"], mode="markers", name="Incidents",
        marker=dict(size=np.clip(np.sqrt(g["n"]) * 3.2, 9, 60), color=CYAN, opacity=.8, line=dict(color=BG, width=2)),
        customdata=g["n"],
        hovertemplate="Unweighted: <b>%{x}</b><br>Weighted: <b>%{y}</b><br>Incidents: %{customdata:,}<extra></extra>",
    ))
    style(fig, 380, legend=True)
    fig.update_layout(legend=dict(orientation="h", y=1.08, font=dict(color=MUTED)))
    fig.update_xaxes(title="Unweighted intensity", dtick=1, range=[-0.5, top + 0.5], title_font=dict(color=MUTED))
    fig.update_yaxes(title="Weighted intensity  (bubble size = incidents)", dtick=1, range=[-0.5, top + 0.5], title_font=dict(color=MUTED))
    return fig, g.rename(columns={"n": "incidents"})


def heatmap(df: pd.DataFrame, min_n: int = 10):
    a = explode(df, "sectors", extra=()).rename(columns={"value": "sector"})
    b = explode(df, "types", extra=()).rename(columns={"value": "attack_type"})
    if a.empty or b.empty:
        return None
    m = a.merge(b, on="incident_id").merge(df[["incident_id", "weighted_intensity"]], on="incident_id")
    g = (m.groupby(["sector", "attack_type"])
         .agg(n=("incident_id", "nunique"), median=("weighted_intensity", "median")).reset_index())
    sector_order = g.groupby("sector")["n"].sum().sort_values(ascending=False).index.tolist()
    type_order = g.groupby("attack_type")["n"].sum().sort_values(ascending=False).index.tolist()
    med = g.pivot(index="sector", columns="attack_type", values="median").reindex(index=sector_order, columns=type_order)
    cnt = g.pivot(index="sector", columns="attack_type", values="n").reindex(index=sector_order, columns=type_order).fillna(0)
    shown = med.where(cnt >= min_n)
    if shown.isna().all().all():
        return None
    text = np.where(cnt.values >= min_n, [[f"{v:g}<br><span style='font-size:10px'>n={int(c)}</span>" if not np.isnan(v) else "" for v, c in zip(rv, rc)] for rv, rc in zip(med.values, cnt.values)], "")
    fig = go.Figure(go.Heatmap(
        z=shown.values, x=[_wrap(c, 14) for c in type_order], y=[_wrap(s, 24) for s in sector_order],
        text=text, texttemplate="%{text}", textfont=dict(color=TEXT, size=12),
        customdata=np.dstack([cnt.values, med.values]),
        colorscale=[[0, "#12283D"], [.5, BLUE], [1, CYAN]], zmin=0, zmax=max(float(np.nanmax(shown.values)), 1),
        xgap=3, ygap=3, hoverongaps=False,
        colorbar=dict(title=dict(text="Median", font=dict(color=MUTED)), tickfont=dict(color=MUTED), thickness=12),
        hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>Median weighted intensity: %{z:g}<br>Incidents (n): %{customdata[0]:.0f}<extra></extra>",
    ))
    style(fig, max(380, 46 * len(sector_order) + 120))
    fig.update_yaxes(autorange="reversed", tickfont=dict(color=TEXT, size=11))
    fig.update_xaxes(side="top", tickfont=dict(color=TEXT, size=11))
    table = g.rename(columns={"n": "incidents", "median": "median_weighted_intensity"})
    table["shown_in_heatmap"] = table["incidents"] >= min_n
    return fig, table.sort_values("incidents", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------- globe
def globe(df: pd.DataFrame, rot_lon: int = 20):
    long = explode(df, "countries", extra=())
    if long.empty:
        return None
    g = long.groupby("value")["incident_id"].nunique().reset_index(name="n")
    g["iso3"] = g["value"].map(ISO3)
    drawn = g.dropna(subset=["iso3"])
    ticks = [t for t in (1, 3, 10, 30, 100, 300, 1000) if t <= max(drawn["n"].max(), 1) * 1.5] or [1]
    fig = go.Figure(go.Choropleth(
        locations=drawn["iso3"], z=np.log10(drawn["n"]), customdata=np.stack([drawn["value"], drawn["n"]], axis=-1),
        colorscale=[[0, "#1B4E73"], [.5, BLUE], [.8, CYAN], [1, AMBER]],
        zmin=0, zmax=max(np.log10(max(ticks[-1], 10)), 1),
        marker_line_color=BG2, marker_line_width=.4,
        colorbar=dict(title=dict(text="Incidents<br>(log scale)", font=dict(color=MUTED, size=11)),
                      tickvals=[np.log10(t) for t in ticks], ticktext=[str(t) for t in ticks],
                      tickfont=dict(color=MUTED), thickness=10, len=.6),
        hovertemplate="<b>%{customdata[0]}</b><br>Documented incidents: %{customdata[1]:,}<extra></extra>",
    ))
    fig.update_geos(
        projection_type="orthographic", projection_rotation=dict(lon=rot_lon, lat=18, roll=0),
        showland=True, landcolor="#10263B", showocean=True, oceancolor="#08182A",
        showcountries=True, countrycolor="rgba(145,166,190,.25)", showcoastlines=True, coastlinecolor="rgba(145,166,190,.35)",
        showlakes=False, showframe=False, bgcolor="rgba(0,0,0,0)", lataxis_showgrid=True, lonaxis_showgrid=True,
        lataxis_gridcolor="rgba(32,217,243,.10)", lonaxis_gridcolor="rgba(32,217,243,.10)",
    )
    style(fig, 520)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), geo=dict(bgcolor="rgba(0,0,0,0)"))
    table = g.sort_values("n", ascending=False).rename(columns={"value": "country", "n": "incidents"})
    return fig, table.reset_index(drop=True), int((~g["iso3"].notna()).sum())


# ---------------------------------------------------------------- radar
def component_scores(row: pd.Series) -> dict[str, float]:
    return {label: component_score(row[col]) for col, label in COMPONENTS.items()}


def radar(scores: dict[str, float]):
    labels = [l.replace(" (", "<br>(").replace("Data theft", "Data<br>theft") for l in scores]
    vals = [0 if np.isnan(v) else v for v in scores.values()]
    hover = [("not available in source" if np.isnan(v) else f"{v:g} point(s)") for v in scores.values()]
    fig = go.Figure(go.Scatterpolar(
        r=vals + vals[:1], theta=labels + labels[:1], fill="toself", mode="lines+markers",
        line=dict(color=CYAN, width=2), fillcolor="rgba(32,217,243,.25)", marker=dict(size=8, color=AMBER, line=dict(color=BG, width=2)),
        customdata=hover + hover[:1], hovertemplate="<b>%{theta}</b><br>%{customdata}<extra></extra>",
    ))
    fig.update_layout(polar=dict(
        bgcolor="rgba(13,27,42,.6)",
        radialaxis=dict(range=[0, 2], tickvals=[0, 1, 2], gridcolor=GRID, linecolor=GRID, tickfont=dict(color=MUTED, size=10)),
        angularaxis=dict(gridcolor=GRID, linecolor=GRID, tickfont=dict(color=TEXT, size=11)),
    ))
    style(fig, 340)
    fig.update_layout(margin=dict(l=90, r=90, t=30, b=30))
    return fig
