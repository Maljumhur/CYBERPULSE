"""Custom CSS + small HTML helpers (cards, KPIs, insight panels)."""
from __future__ import annotations

import html as _html

import streamlit as st

CYAN, BLUE, VIOLET, AMBER = "#20D9F3", "#3478F6", "#8265FF", "#FFC857"
BG, BG2, CARD = "#07111F", "#0D1B2A", "#12283D"
TEXT, MUTED = "#F2F7FF", "#91A6BE"

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
:root {{
  --bg:{BG}; --bg2:{BG2}; --card:{CARD}; --cyan:{CYAN}; --blue:{BLUE}; --violet:{VIOLET};
  --amber:{AMBER}; --text:{TEXT}; --muted:{MUTED}; --line:rgba(145,166,190,.18);
}}
html, body, [class*="css"], .stApp {{ font-family:'Inter',system-ui,-apple-system,'Segoe UI',sans-serif; }}
.stApp {{
  background:
    radial-gradient(1200px 600px at 85% -10%, rgba(130,101,255,.16), transparent 60%),
    radial-gradient(900px 500px at 5% 0%, rgba(32,217,243,.12), transparent 55%),
    var(--bg);
  color:var(--text);
}}
header[data-testid="stHeader"] {{ background:transparent; }}
.block-container {{ padding-top:1.6rem; max-width:1320px; }}
section[data-testid="stSidebar"] {{ background:var(--bg2); border-right:1px solid var(--line); }}
section[data-testid="stSidebar"] .block-container {{ padding-top:1rem; }}
h1,h2,h3,h4 {{ letter-spacing:-.01em; color:var(--text); }}

/* hero */
.hero {{
  position:relative; overflow:hidden; border-radius:22px; padding:30px 34px; margin-bottom:18px;
  border:1px solid var(--line);
  background:
    linear-gradient(135deg, rgba(32,217,243,.10), rgba(130,101,255,.10) 60%, rgba(52,120,246,.08)),
    linear-gradient(var(--line) 1px, transparent 1px) 0 0/44px 44px,
    linear-gradient(90deg, var(--line) 1px, transparent 1px) 0 0/44px 44px,
    var(--bg2);
  box-shadow:0 24px 60px -30px rgba(32,217,243,.35), inset 0 1px 0 rgba(255,255,255,.05);
  animation:rise .7s ease both;
}}
.hero:after {{ content:""; position:absolute; right:-80px; top:-80px; width:300px; height:300px; border-radius:50%;
  background:radial-gradient(circle at 35% 35%, rgba(32,217,243,.35), rgba(52,120,246,.12) 55%, transparent 70%);
  filter:blur(2px); animation:float 9s ease-in-out infinite; }}
.hero .eyebrow {{ font:600 12px 'JetBrains Mono',monospace; letter-spacing:.22em; color:var(--cyan); text-transform:uppercase; }}
.hero h1 {{ margin:.25rem 0 .2rem; font-size:2.6rem; font-weight:800; line-height:1.05;
  background:linear-gradient(90deg,#fff,var(--cyan) 55%,var(--violet)); -webkit-background-clip:text; background-clip:text; color:transparent; }}
.hero .tag {{ color:var(--muted); font-size:1.05rem; max-width:760px; margin:0; }}
.hero .rq {{ margin-top:14px; display:inline-block; padding:8px 14px; border-radius:999px; border:1px solid rgba(32,217,243,.35);
  background:rgba(32,217,243,.08); color:var(--text); font-size:.92rem; position:relative; z-index:1; }}
.hero .rq b {{ color:var(--cyan); }}

/* KPI cards - 3D tilt + staggered reveal */
.kpi-row {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(112px,1fr)); gap:14px; margin:6px 0 18px; perspective:1000px; }}
.kpi {{
  position:relative; border-radius:16px; padding:14px 14px; border:1px solid var(--line);
  background:linear-gradient(160deg, rgba(18,40,61,.95), rgba(13,27,42,.95));
  box-shadow:0 18px 40px -24px rgba(0,0,0,.8), inset 0 1px 0 rgba(255,255,255,.06);
  transform:rotateX(4deg); transform-origin:50% 100%;
  transition:transform .35s ease, box-shadow .35s ease, border-color .35s ease;
  animation:reveal .7s cubic-bezier(.2,.8,.2,1) both; animation-delay:var(--d,0s);
}}
.kpi:hover {{ transform:translateY(-6px) rotateX(0deg); border-color:rgba(32,217,243,.55);
  box-shadow:0 26px 50px -22px rgba(32,217,243,.45), inset 0 1px 0 rgba(255,255,255,.08); }}
.kpi-label {{ color:var(--muted); font-size:.74rem; letter-spacing:.14em; text-transform:uppercase; font-weight:600; }}
.kpi-value {{ font:700 1.9rem 'JetBrains Mono',monospace; color:var(--text); margin:.15rem 0; text-shadow:0 0 24px rgba(32,217,243,.35); }}
.kpi-sub {{ color:var(--muted); font-size:.8rem; }}
.kpi.accent .kpi-value {{ color:var(--amber); text-shadow:0 0 24px rgba(255,200,87,.35); }}

/* generic glass cards */
.glass {{ border-radius:16px; padding:16px 18px; border:1px solid var(--line); background:rgba(18,40,61,.72);
  backdrop-filter:blur(6px); transition:transform .3s ease, border-color .3s ease, box-shadow .3s ease; height:100%; }}
.glass:hover {{ transform:translateY(-4px); border-color:rgba(32,217,243,.45); box-shadow:0 20px 40px -26px rgba(32,217,243,.5); }}
.glass h4 {{ margin:0 0 6px; font-size:1rem; }}
.glass p, .glass li {{ color:var(--muted); font-size:.9rem; line-height:1.5; margin:0; }}
.glass .num {{ font:700 .8rem 'JetBrains Mono',monospace; color:var(--cyan); letter-spacing:.12em; }}
.grid {{ display:grid; gap:14px; grid-template-columns:repeat(auto-fit,minmax(230px,1fr)); }}

/* section headings */
.sec-title {{ display:flex; align-items:center; gap:10px; margin:8px 0 2px; }}
.sec-title .chip {{ font:700 .75rem 'JetBrains Mono',monospace; color:var(--bg); background:var(--cyan); padding:3px 9px; border-radius:6px; }}
.sec-title h2 {{ margin:0; font-size:1.55rem; }}
.sec-sub {{ color:var(--muted); margin:0 0 14px; }}

/* insight panel */
.insight {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:10px; margin:2px 0 26px; }}
.insight .cell {{ border-radius:12px; padding:12px 14px; border:1px solid var(--line); background:rgba(13,27,42,.8); font-size:.88rem; line-height:1.5; color:var(--text); }}
.insight .cell h5 {{ margin:0 0 4px; font:700 .7rem 'JetBrains Mono',monospace; letter-spacing:.14em; text-transform:uppercase; }}
.insight .what {{ border-left:3px solid var(--cyan); }} .insight .what h5 {{ color:var(--cyan); }}
.insight .why {{ border-left:3px solid var(--violet); }} .insight .why h5 {{ color:#A593FF; }}
.insight .careful {{ border-left:3px solid var(--amber); }} .insight .careful h5 {{ color:var(--amber); }}
.scope {{ display:inline-block; font:600 .68rem 'JetBrains Mono',monospace; letter-spacing:.1em; text-transform:uppercase;
  padding:3px 9px; border-radius:999px; margin:0 0 6px; border:1px solid var(--line); color:var(--muted); }}
.scope.live {{ color:var(--cyan); border-color:rgba(32,217,243,.4); }}
.scope.full {{ color:var(--amber); border-color:rgba(255,200,87,.45); }}

.pill {{ display:inline-block; padding:2px 10px; margin:2px 4px 2px 0; border-radius:999px; font-size:.78rem;
  border:1px solid rgba(32,217,243,.35); background:rgba(32,217,243,.08); color:var(--text); }}
.pill.warn {{ border-color:rgba(255,200,87,.5); background:rgba(255,200,87,.1); color:var(--amber); }}
.pill.muted {{ border-color:var(--line); background:transparent; color:var(--muted); }}
.warnbox {{ border-radius:12px; padding:10px 14px; border:1px solid rgba(255,200,87,.5); background:rgba(255,200,87,.08); color:var(--text); margin:8px 0; }}
.dossier-name {{ font-size:1.25rem; font-weight:700; margin:.2rem 0 .4rem; }}
.fact {{ display:flex; justify-content:space-between; gap:16px; padding:7px 0; border-bottom:1px dashed var(--line); font-size:.88rem; }}
.fact span:first-child {{ color:var(--muted); }} .fact span:last-child {{ text-align:right; max-width:62%; }}
.na {{ color:var(--muted); font-style:italic; }}

/* tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; border-bottom:1px solid var(--line); flex-wrap:wrap; }}
.stTabs [data-baseweb="tab"] {{ border-radius:10px 10px 0 0; padding:10px 16px; color:var(--muted); font-weight:600; }}
.stTabs [aria-selected="true"] {{ color:var(--cyan) !important; background:rgba(32,217,243,.08); }}
.stTabs [data-baseweb="tab-highlight"] {{ background:var(--cyan); }}
.stButton>button, .stDownloadButton>button {{ border-radius:10px; border:1px solid rgba(32,217,243,.45); background:rgba(32,217,243,.08); color:var(--text); }}
.stButton>button:hover, .stDownloadButton>button:hover {{ border-color:var(--cyan); color:var(--cyan); }}
.footer {{ color:var(--muted); font-size:.8rem; text-align:center; margin:30px 0 8px; }}

@keyframes reveal {{ from {{ opacity:0; transform:translateY(18px) rotateX(18deg); filter:blur(6px); }} to {{ opacity:1; }} }}
@keyframes rise {{ from {{ opacity:0; transform:translateY(12px); }} to {{ opacity:1; transform:none; }} }}
@keyframes float {{ 0%,100% {{ transform:translate(0,0); }} 50% {{ transform:translate(-14px,12px); }} }}
@media (prefers-reduced-motion: reduce) {{
  *, *:before, *:after {{ animation:none !important; transition:none !important; }}
  .kpi {{ transform:none; }}
}}
@media (max-width: 700px) {{ .hero h1 {{ font-size:1.8rem; }} .hero {{ padding:22px 20px; }} }}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def esc(x) -> str:
    return _html.escape(str(x))


def md_html(s: str) -> None:
    """Render an HTML snippet (indentation stripped so Markdown never turns it into a code block)."""
    st.markdown(" ".join(l.strip() for l in s.splitlines() if l.strip()), unsafe_allow_html=True)


def hero() -> None:
    md_html(f"""
    <div class="hero">
      <div class="eyebrow">Global Cyber Threat Intelligence · historical analysis</div>
      <h1>CYBERPULSE</h1>
      <p class="tag">Decoding the patterns of cyber conflict — a data-driven exploration of documented incidents from the
      EuRepoC Global Cyber Incidents dataset (v1.3).</p>
      <div class="rq"><b>Research question</b> · Who gets targeted, how, and with what documented impact?</div>
    </div>""")


def section_title(code: str, title: str, subtitle: str) -> None:
    md_html(f"""<div class="sec-title"><span class="chip">{esc(code)}</span><h2>{esc(title)}</h2></div>
    <p class="sec-sub">{esc(subtitle)}</p>""")


def kpi_row(items: list[tuple[str, str, str, bool]]) -> None:
    cells = []
    for i, (label, value, sub, accent) in enumerate(items):
        cells.append(
            f'<div class="kpi{" accent" if accent else ""}" style="--d:{0.07 * i:.2f}s">'
            f'<div class="kpi-label">{esc(label)}</div><div class="kpi-value">{esc(value)}</div>'
            f'<div class="kpi-sub">{esc(sub)}</div></div>'
        )
    md_html(f'<div class="kpi-row">{"".join(cells)}</div>')


def insight_panel(ins: dict) -> None:
    """ins: what/why/careful strings (already escaped-safe plain text) and scope in {'live','full'}."""
    scope = ins.get("scope", "live")
    tag = (
        '<span class="scope live">● Updates with your filters</span>'
        if scope == "live"
        else '<span class="scope full">◆ Full-dataset finding · does not change with filters</span>'
    )
    md_html(f"""{tag}
    <div class="insight">
      <div class="cell what"><h5>What happened</h5>{esc(ins['what'])}</div>
      <div class="cell why"><h5>Why it matters</h5>{esc(ins['why'])}</div>
      <div class="cell careful"><h5>Be careful</h5>{esc(ins['careful'])}</div>
    </div>""")
