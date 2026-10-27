"""CYBERPULSE — Global Cyber Threat Intelligence ("Decoding the Patterns of Cyber Conflict").
Streamlit dashboard over the cleaned EuRepoC Global Cyber Incidents v1.3 export.
Historical analysis only: nothing here is live, simulated or imputed."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components import charts, insights
from components.data import COMPONENTS, FIRST_CLEAN_COL, ISO3, explode, load_data, ordered_counts, raw_columns
from components.filters import apply_filters, render_sidebar
from components.styles import esc, hero, inject_css, insight_panel, kpi_row, md_html, section_title

st.set_page_config(page_title="CYBERPULSE — Global Cyber Threat Intelligence", page_icon="🛰️",
                   layout="wide", initial_sidebar_state="expanded")
inject_css()
PLOT_CFG = {"displaylogo": False, "modeBarButtonsToRemove": ["lasso2d", "select2d"]}

full = load_data()
TOTAL = full["incident_id"].nunique()
fs = render_sidebar(full)
df = apply_filters(full, fs)
N = df["incident_id"].nunique()

hero()
if fs.is_active():
    st.caption(f"Active filters: {' · '.join(fs.summary())} — showing **{N:,}** of {TOTAL:,} incidents.")
if N == 0:
    st.warning("No incidents match the current filters. Widen the ranges or press **Reset all filters** in the sidebar.")
    st.stop()


def show(result, ins, table_label="View the data behind this chart", note=None):
    """Render chart + insight panel + accessible table. result = (fig, table, ...) or None."""
    if result is None:
        st.info("Not enough data in this view for this chart. Try widening the filters.")
        return
    fig, table = result[0], result[1]
    st.session_state["_k"] = st.session_state.get("_k", 0) + 1
    st.plotly_chart(fig, width="stretch", config=PLOT_CFG, key=f"chart_{st.session_state['_k']}")
    if note:
        st.caption(note)
    with st.expander(table_label):
        st.dataframe(table, hide_index=True, width="stretch")
    insight_panel(ins)


tabs = st.tabs(["🛰️ Mission Control", "📈 Threat Landscape", "🎯 Target Intelligence",
                "⚡ Intensity Lab", "🧬 Incident Explorer", "🧭 Behind the Intelligence"])

# ============================================================== A. Mission Control
with tabs[0]:
    section_title("A", "Mission Control", "The headline picture for the current selection.")
    types_n = ordered_counts(df, "types")
    sect_n = ordered_counts(df, "sectors")
    ctry_n = ordered_counts(df, "countries")
    yr = df.dropna(subset=["year"]).groupby("year")["incident_id"].nunique()
    kpi_row([
        ("Incidents in view", f"{N:,}", f"of {TOTAL:,} in dataset", True),
        ("Attack types", f"{len(types_n)}", "distinct in view", False),
        ("Target sectors", f"{len(sect_n)}", "distinct in view", False),
        ("Countries / territories", f"{len(ctry_n)}", "valid targets in view", False),
        ("Median intensity", f"{df['weighted_intensity'].median():g}", "weighted, dataset score", False),
        ("Peak year", f"{int(yr.idxmax())}" if len(yr) else "n/a", "known start date only", False),
    ])
    c1, c2 = st.columns([1.35, 1])
    with c1:
        st.markdown("##### Documented incidents by target country")
        rot = st.slider("Rotate globe (longitude)", -180, 180, 20, key="rot",
                        help="Drag the globe, or use this slider.")
        res = charts.globe(df, rot)
        if res:
            st.plotly_chart(res[0], width="stretch", config=PLOT_CFG, key="globe")
            with st.expander("View the data behind the globe"):
                st.dataframe(res[1], hide_index=True, width="stretch")
            insight_panel(insights.map_insight(df, res[2], int(df["_countries"].map(len).eq(0).sum())))
        else:
            st.info("No valid target countries in this view.")
    with c2:
        st.markdown("##### Incidents by start year")
        res = charts.year_chart(df, "Frequency")
        if res:
            st.plotly_chart(res[0], width="stretch", config=PLOT_CFG, key="mc_year")
        st.markdown("##### Headline signals (this view)")
        top = lambda s: f"{s.index[0]} ({int(s.iloc[0]):,})" if len(s) else "n/a"
        md_html(f"""<div class="grid" style="grid-template-columns:1fr">
          <div class="glass"><h4>Most common attack type</h4><p>{esc(top(types_n))}</p></div>
          <div class="glass"><h4>Most targeted sector</h4><p>{esc(top(sect_n))}</p></div>
          <div class="glass"><h4>Most documented target country</h4><p>{esc(top(ctry_n))}</p></div></div>""")
    with st.expander("🧭 Guided Intelligence Tour"):
        steps = {
            "1 · Who": "Open **Target Intelligence** — which sectors and countries appear most in the documented record?",
            "2 · How": "Open **Threat Landscape** — which attack types dominate, and when did documentation grow?",
            "3 · Impact": "Open **Intensity Lab** — how severe are incidents by method and sector? Use the heatmap's sample counts.",
            "4 · Zoom in": "Open **Incident Explorer** — pick one incident and read its Incident DNA dossier.",
            "5 · Trust": "Open **Behind the Intelligence** — see how the data was cleaned and what it can't tell you.",
        }
        step = st.radio("Tour step", list(steps), horizontal=True, label_visibility="collapsed")
        st.info(steps[step])
    md_html("""<div class="warnbox"><b>Read this first.</b> CYBERPULSE is a historical analysis of a curated repository —
    not live monitoring. Counts reflect documented incidents, not national risk or total cyber activity.</div>""")

# ============================================================== B. Threat Landscape
with tabs[1]:
    section_title("B", "Threat Landscape", "How attacks unfold over time and by method.")
    metric = st.radio("View", ["Frequency", "Intensity"], horizontal=True, key="metric_b",
                      help="Frequency = unique incidents. Intensity = median weighted intensity (with sample counts).")
    st.markdown("#### Incidents over time" if metric == "Frequency" else "#### Median intensity over time")
    show(charts.year_chart(df, metric), insights.year_insight(df, metric))
    st.markdown("#### Attack types")
    show(charts.category_bar(df, "types", metric, top_n=10), insights.category_insight(
        df, "types", metric, "attack type", filter_active=bool(fs.types)))

# ============================================================== C. Target Intelligence
with tabs[2]:
    section_title("C", "Target Intelligence", "Who is documented as being targeted.")
    metric_c = st.radio("View", ["Frequency", "Intensity"], horizontal=True, key="metric_c")
    st.markdown("#### Target sectors")
    show(charts.category_bar(df, "sectors", metric_c, top_n=10), insights.category_insight(
        df, "sectors", metric_c, "sector", filter_active=bool(fs.sectors)))
    st.markdown("#### Top target countries / territories")
    top_n = st.slider("Countries to show", 5, 20, 10, key="topn")
    show(charts.category_bar(df, "countries", metric_c, top_n=top_n, min_n=10 if metric_c == "Intensity" else 1),
         insights.country_insight(df, metric_c),
         note="Intensity view only includes countries with at least 10 incidents." if metric_c == "Intensity" else None)

# ============================================================== D. Intensity Lab
with tabs[3]:
    section_title("D", "Intensity Lab", "How documented impact varies. Weighted intensity is a dataset-specific score, not financial loss.")
    st.markdown("#### Distribution of weighted intensity")
    show(charts.intensity_hist(df), insights.hist_insight(df))
    st.markdown("#### Attack type vs intensity")
    show(charts.type_box(df), insights.box_insight(df))
    st.markdown("#### Unweighted vs weighted intensity")
    show(charts.scatter_bubble(df), insights.scatter_insight(df))
    st.markdown("#### Sector × attack type: median intensity")
    min_n = st.slider("Minimum incidents per cell", 1, 50, 10, key="heat_n",
                      help="Cells below this sample size are blank — medians of tiny samples mislead.")
    show(charts.heatmap(df, min_n), insights.heatmap_insight(df, min_n))
    f = insights.full_dataset_findings(full)
    st.markdown("#### Verified full-dataset findings")
    insight_panel(dict(
        scope="full",
        what=(f"Across all {TOTAL:,} incidents: disruption incidents have a median weighted intensity of "
              f"{f['disruption_ci']:g} in Critical infrastructure and {f['disruption_edu']:g} in Education, versus "
              f"{f['disruption_state']:g} in State institutions. {f['top_type']} has the highest median overall ({f['top_type_median']:g}); "
              f"{100 * f['hijack_share_1']:.0f}% of Hijacking-without-Misuse incidents score exactly 1."),
        why="Where disruption is documented against essential services or education it tends to score higher.",
        careful="Recomputed from the unfiltered dataset; these numbers will not move with your filters. Association, not cause."))

# ============================================================== E. Incident Explorer
with tabs[4]:
    section_title("E", "Incident Explorer", "Browse incidents in the current view and open an Incident DNA dossier.")
    q = st.text_input("Search incident name or description", placeholder="e.g. ransomware, hospital, election")
    view = df
    if q.strip():
        t = q.strip().lower()
        view = df[df["name"].fillna("").str.lower().str.contains(t, regex=False)
                  | df["description"].fillna("").str.lower().str.contains(t, regex=False)]
    order = st.selectbox("Sort by", ["Weighted intensity (high→low)", "Start date (newest)", "Start date (oldest)", "Incident ID"])
    view = {"Weighted intensity (high→low)": lambda d: d.sort_values(["weighted_intensity", "incident_id"], ascending=[False, True]),
            "Start date (newest)": lambda d: d.sort_values("start_date_clean", ascending=False, na_position="last"),
            "Start date (oldest)": lambda d: d.sort_values("start_date_clean", na_position="last"),
            "Incident ID": lambda d: d.sort_values("incident_id")}[order](view)
    st.caption(f"{len(view):,} incident(s) match.")
    cols = ["incident_id", "name", "start_date_clean", "incident_type_clean", "receiver_category_clean",
            "receiver_country_valid", "weighted_intensity", "unweighted_intensity", "date_error"]
    st.dataframe(view[cols].head(500).assign(name=lambda d: d["name"].str.strip(),
                 start_date_clean=lambda d: d["start_date_clean"].dt.strftime("%Y-%m-%d")), hide_index=True, width="stretch", height=300)
    if len(view) > 500:
        st.caption("Table shows the first 500 rows; the download below contains everything in view.")
    if len(view):
        ids = view["incident_id"].head(500).tolist()
        lookup = view.set_index("incident_id")["name"].str.strip()
        pick = st.selectbox("Open an incident dossier", ids, format_func=lambda i: f"{i} · {lookup[i][:90]}")
        r = full.loc[full["incident_id"] == pick].iloc[0]
        na = '<span class="na">not available</span>'
        val = lambda x: esc(x) if isinstance(x, str) and x.strip() and x != "Not available" else na
        st.markdown("### 🧬 Incident DNA")
        if bool(r["date_error"]):
            md_html(f"""<div class="warnbox">⚠ <b>Inconsistent dates.</b> This record ends ({r['end_date_clean']:%Y-%m-%d}) before it starts
            ({r['start_date_clean']:%Y-%m-%d}) in the source. It is flagged, not corrected.</div>""")
        d1, d2, d3 = st.columns([1.1, 1, 1])
        with d1:
            md_html(f"""<div class="glass"><span class="pill">ID {int(r['incident_id'])}</span>
              <div class="dossier-name">{esc(str(r['name']).strip())}</div>
              {''.join(f'<span class="pill">{esc(t)}</span>' for t in r['_types']) or '<span class="pill muted">type n/a</span>'}
              {''.join(f'<span class="pill warn">{esc(t)}</span>' for t in r['_sectors'])}
              {''.join(f'<span class="pill muted">{esc(t)}</span>' for t in r['_countries'])}</div>""")
            st.markdown(f"**Description**\n\n{r['description'] if isinstance(r['description'], str) else '_not available_'}")
        with d2:
            st.plotly_chart(charts.radar(charts.component_scores(r)), width="stretch", config=PLOT_CFG, key="radar")
            st.caption("Points per intensity component (0–2). Components marked “not available” in the source plot as 0 — missing is not zero.")
        with d3:
            sd = f"{r['start_date_clean']:%Y-%m-%d}" if pd.notna(r["start_date_clean"]) else "unknown"
            ed = f"{r['end_date_clean']:%Y-%m-%d}" if pd.notna(r["end_date_clean"]) else "unknown"
            facts = [("Start / end", f"{sd} → {ed}"), ("Weighted intensity", int(r["weighted_intensity"])),
                     ("Unweighted intensity", int(r["unweighted_intensity"])), ("Initiator", val(r["initiator_category"])),
                     ("Functional impact", val(r["functional_impact"])), ("Intelligence impact", val(r["intelligence_impact"])),
                     ("MITRE initial access", val(r["mitre_initial_access"])), ("MITRE impact", val(r["mitre_impact"]))]
            md_html(f'<div class="glass">{"".join(f"<div class=fact><span>{esc(k)}</span><span>{v if k not in ("Start / end","Weighted intensity","Unweighted intensity") else esc(v)}</span></div>" for k, v in facts)}</div>')
        srcs = [u.strip() for u in str(r["source_url"]).split(";") if u.strip().startswith("http")]
        if srcs:
            with st.expander(f"Sources ({len(srcs)})"):
                for u in srcs[:8]:
                    st.markdown(f"- {u}")
    st.divider()
    st.markdown("#### Data preview, summary and download")
    keep = [c for c in raw_columns(full) if c in df.columns]
    out = df[keep].copy()
    for c in ("start_date_clean", "end_date_clean"):
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    p1, p2 = st.columns([1.6, 1])
    with p1:
        st.dataframe(out.head(25), hide_index=True, width="stretch", height=260)
    with p2:
        st.dataframe(df[["weighted_intensity", "unweighted_intensity"]].describe().round(2), width="stretch")
        miss = {"Attack type": df["incident_type_clean"], "Sector": df["receiver_category_clean"],
                "Country": df["receiver_country_valid"], "Start date": df["start_date_clean"]}
        st.dataframe(pd.DataFrame({"missing in view": {k: int(v.isna().sum()) for k, v in miss.items()}}), width="stretch")
    st.download_button("⬇ Download filtered data (CSV)", out.to_csv(index=False).encode("utf-8"),
                       file_name="cyberpulse_filtered_incidents.csv", mime="text/csv")

# ============================================================== F. Behind the Intelligence
with tabs[5]:
    section_title("F", "Behind the Intelligence", "How the data was prepared, what was verified, and what it cannot tell you.")
    raw_n = len(raw_columns(full)[:raw_columns(full).index(FIRST_CLEAN_COL)])
    miss = lambda c: int(full[c].isna().sum())
    bad = full[full["date_error"]]
    bad_txt = "; ".join(f"ID {int(r.incident_id)} (start {r.start_date_clean:%Y-%m-%d}, end {r.end_date_clean:%Y-%m-%d})" for r in bad.itertuples())
    journey = [
        ("01", "Data Understanding", f"{TOTAL:,} incident records, {raw_n} original EuRepoC columns (v1.3). Multi-value fields use “;” separators."),
        ("02", "Data Quality Assessment", f"Missing after cleaning: attack type {miss('incident_type_clean')}, sector {miss('receiver_category_clean')}, valid country {miss('receiver_country_valid')}, start date {miss('start_date_clean')}, end date {miss('end_date_clean')}. Missing values are preserved, not filled."),
        ("03", "Data Cleaning", "Focused cleaning only: split on “;”, trimmed, removed “Not available”/“Unknown”/blank and duplicates in the type, country and sector fields; regions and organisations (e.g. NATO, UN, EU institutions) excluded from the country field; territories such as Taiwan, Hong Kong and Palestine kept. Other columns were not exhaustively cleaned."),
        ("04", "Date Validation", f"Dates parsed as day.month.year. {len(bad)} record(s) have an end date before the start date and are flagged, not altered: {bad_txt}."),
        ("05", "EDA & Insights", "Counts use unique incident IDs; intensity is analysed with medians and sample sizes. See the Intensity Lab for the verified full-dataset findings."),
    ]
    md_html(f'<div class="grid">{"".join(f"<div class=glass><div class=num>STEP {n}</div><h4>{esc(t)}</h4><p>{esc(d)}</p></div>" for n, t, d in journey)}</div>')

    st.markdown("#### Verified figures — notebook vs. recomputed from the CSV")
    ac = ordered_counts(full, "types")
    sc = ordered_counts(full, "sectors")
    cc = ordered_counts(full, "countries")
    yy = full.dropna(subset=["year"]).groupby("year")["incident_id"].nunique()
    wi = full["weighted_intensity"].value_counts()
    checks = [
        ("Incidents", 3414, TOTAL), ("Attack types", 6, len(ac)), ("Sectors", 10, len(sc)),
        ("Peak year (known start date)", 2023, int(yy.idxmax())),
        ("Incidents 2021", 160, int(yy[2021])), ("Incidents 2022", 354, int(yy[2022])),
        ("Incidents 2023", 723, int(yy[2023])), ("Incidents 2024", 700, int(yy[2024])),
        ("Top sector count", 1770, int(sc.iloc[0])), ("2nd sector count", 1383, int(sc.iloc[1])), ("3rd sector count", 540, int(sc.iloc[2])),
        ("Attack-type counts", "1800 / 1475 / 1261 / 502 / 414 / 365", " / ".join(str(int(v)) for v in ac.values)),
        ("US / Russia / Germany / UK / Israel", "871 / 220 / 171 / 165 / 149", " / ".join(str(int(v)) for v in cc.head(5).values)),
        ("Most common weighted intensity (incidents)", "1 (1,250)", f"{int(wi.idxmax())} ({int(wi.max()):,})"),
        ("Incidents with intensity 1–4", 3167, int(full['weighted_intensity'].between(1, 4).sum())),
        ("Max weighted intensity", 11, int(full["weighted_intensity"].max())),
        ("Inconsistent date records", 2, int(full["date_error"].sum())),
    ]
    tbl = pd.DataFrame([{"Figure": a, "Notebook": str(b), "Recomputed": str(c), "Match": "✅" if str(b) == str(c) else "❌"} for a, b, c in checks])
    st.dataframe(tbl, hide_index=True, width="stretch")

    st.markdown("#### What this dashboard cannot tell you")
    md_html("""<div class="grid">
      <div class="glass"><h4>Not live</h4><p>A historical repository. No real-time monitoring, no fabricated attack lines or geolocations.</p></div>
      <div class="glass"><h4>Counts ≠ risk</h4><p>Country and sector counts are raw, not normalised by size or economy, and reflect documentation effort.</p></div>
      <div class="glass"><h4>Overlapping categories</h4><p>One incident can have several types, sectors or countries, so category totals exceed incident totals.</p></div>
      <div class="glass"><h4>Intensity is not loss</h4><p>Weighted intensity is a dataset-specific ordinal score, not a financial or human-cost estimate.</p></div>
      <div class="glass"><h4>Missing stays missing</h4><p>Unknown dates, countries and components are never imputed; they are excluded from the relevant chart and counted.</p></div>
      <div class="glass"><h4>Focused cleaning</h4><p>Only the analysis fields were cleaned; other columns are as published.</p></div></div>""")
    st.caption("Data: EuRepoC — European Repository of Cyber Incidents, Global Cyber Incidents v1.3. Check EuRepoC's terms before redistributing the data.")

md_html('<div class="footer">CYBERPULSE · historical analysis of the EuRepoC Global Cyber Incidents dataset · built with Streamlit &amp; Plotly</div>')
