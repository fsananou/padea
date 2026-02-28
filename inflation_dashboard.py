#!/usr/bin/env python3
"""
CPI & Oil Price Dashboard
Sources: IMF World Economic Outlook (CPI) · FRED (Brent / WTI crude oil)
"""

# ── Auto-launch when executed directly ────────────────────────────────────────
import sys, os
if __name__ == "__main__" and "streamlit" not in sys.modules:
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)],
        check=False,
    )
    sys.exit(0)

# ── Imports ────────────────────────────────────────────────────────────────────
import io
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CPI & Oil Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark / glassmorphism CSS ───────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global background ─────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(160deg, #07101f 0%, #0c1a2e 60%, #07101f 100%);
}
/* ── Sidebar ────────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0b1726 0%, #0e2038 100%);
    border-right: 1px solid rgba(56,189,248,0.1);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] .stSelectbox label {
    color: rgba(226,232,240,0.85) !important;
}
/* ── Tabs ────────────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: rgba(255,255,255,0.025);
    border-radius: 14px;
    padding: 6px;
    border: 1px solid rgba(56,189,248,0.1);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    padding: 8px 22px;
    color: rgba(226,232,240,0.45);
    font-weight: 500;
    font-size: 0.9rem;
    letter-spacing: 0.02em;
    transition: all .2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, rgba(56,189,248,0.18), rgba(99,102,241,0.14)) !important;
    color: #38BDF8 !important;
    border: 1px solid rgba(56,189,248,0.28) !important;
}
/* ── Metric cards ────────────────────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(56,189,248,0.12);
    border-radius: 16px;
    padding: 1rem 1.3rem;
    backdrop-filter: blur(8px);
}
[data-testid="stMetric"] label {
    color: rgba(148,163,184,0.85) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: #38BDF8 !important;
    font-size: 1.75rem !important;
    font-weight: 700 !important;
}
/* ── Dividers & headings ─────────────────────────────────────────────────────── */
hr { border-color: rgba(56,189,248,0.1) !important; }
h1, h2, h3, h4 { color: #e2e8f0 !important; }
p, li { color: rgba(226,232,240,0.7) !important; }
/* ── Block container ─────────────────────────────────────────────────────────── */
.block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
/* ── Expanders ───────────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(56,189,248,0.1) !important;
    border-radius: 12px;
}
/* ── Progress bar ────────────────────────────────────────────────────────────── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #38BDF8, #818CF8);
}
/* ── DataFrames ──────────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(56,189,248,0.1);
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY CATALOG  (weo = IMF WEO ISO-3 or area code)
# ─────────────────────────────────────────────────────────────────────────────
COUNTRIES: dict[str, dict] = {
    # ── Advanced ───────────────────────────────────────────────────────────────
    "United States":   {"weo": "USA"},
    "Euro Area":       {"weo": "EURO"},
    "Germany":         {"weo": "DEU"},
    "France":          {"weo": "FRA"},
    "Italy":           {"weo": "ITA"},
    "Spain":           {"weo": "ESP"},
    "Netherlands":     {"weo": "NLD"},
    "Belgium":         {"weo": "BEL"},
    "Austria":         {"weo": "AUT"},
    "Portugal":        {"weo": "PRT"},
    "Greece":          {"weo": "GRC"},
    "Ireland":         {"weo": "IRL"},
    "Finland":         {"weo": "FIN"},
    "Luxembourg":      {"weo": "LUX"},
    "Slovakia":        {"weo": "SVK"},
    "Slovenia":        {"weo": "SVN"},
    "Estonia":         {"weo": "EST"},
    "Latvia":          {"weo": "LVA"},
    "Lithuania":       {"weo": "LTU"},
    "Croatia":         {"weo": "HRV"},
    "United Kingdom":  {"weo": "GBR"},
    "Japan":           {"weo": "JPN"},
    "Canada":          {"weo": "CAN"},
    "Australia":       {"weo": "AUS"},
    "New Zealand":     {"weo": "NZL"},
    "Switzerland":     {"weo": "CHE"},
    "Sweden":          {"weo": "SWE"},
    "Norway":          {"weo": "NOR"},
    "Denmark":         {"weo": "DNK"},
    "Iceland":         {"weo": "ISL"},
    # ── Eastern Europe ────────────────────────────────────────────────────────
    "Poland":          {"weo": "POL"},
    "Czech Republic":  {"weo": "CZE"},
    "Hungary":         {"weo": "HUN"},
    "Romania":         {"weo": "ROU"},
    "Bulgaria":        {"weo": "BGR"},
    # ── Asia-Pacific ──────────────────────────────────────────────────────────
    "China":           {"weo": "CHN"},
    "India":           {"weo": "IND"},
    "South Korea":     {"weo": "KOR"},
    "Indonesia":       {"weo": "IDN"},
    "Malaysia":        {"weo": "MYS"},
    "Thailand":        {"weo": "THA"},
    "Philippines":     {"weo": "PHL"},
    "Vietnam":         {"weo": "VNM"},
    "Singapore":       {"weo": "SGP"},
    "Pakistan":        {"weo": "PAK"},
    "Bangladesh":      {"weo": "BGD"},
    # ── Latin America ─────────────────────────────────────────────────────────
    "Brazil":          {"weo": "BRA"},
    "Mexico":          {"weo": "MEX"},
    "Argentina":       {"weo": "ARG"},
    "Chile":           {"weo": "CHL"},
    "Colombia":        {"weo": "COL"},
    "Peru":            {"weo": "PER"},
    "Bolivia":         {"weo": "BOL"},
    "Ecuador":         {"weo": "ECU"},
    "Uruguay":         {"weo": "URY"},
    "Paraguay":        {"weo": "PRY"},
    "Venezuela":       {"weo": "VEN"},
    # ── Middle East & North Africa ────────────────────────────────────────────
    "Saudi Arabia":    {"weo": "SAU"},
    "UAE":             {"weo": "ARE"},
    "Turkey":          {"weo": "TUR"},
    "Israel":          {"weo": "ISR"},
    "Egypt":           {"weo": "EGY"},
    "Morocco":         {"weo": "MAR"},
    "Tunisia":         {"weo": "TUN"},
    "Algeria":         {"weo": "DZA"},
    "Libya":           {"weo": "LBY"},
    "Iran":            {"weo": "IRN"},
    "Iraq":            {"weo": "IRQ"},
    "Jordan":          {"weo": "JOR"},
    "Lebanon":         {"weo": "LBN"},
    # ── Sub-Saharan Africa ────────────────────────────────────────────────────
    "South Africa":    {"weo": "ZAF"},
    "Nigeria":         {"weo": "NGA"},
    "Kenya":           {"weo": "KEN"},
    "Ethiopia":        {"weo": "ETH"},
    "Ghana":           {"weo": "GHA"},
    "Tanzania":        {"weo": "TZA"},
    "Uganda":          {"weo": "UGA"},
    "Mozambique":      {"weo": "MOZ"},
    "Côte d'Ivoire":   {"weo": "CIV"},
    "Senegal":         {"weo": "SEN"},
    "Cameroon":        {"weo": "CMR"},
    "Angola":          {"weo": "AGO"},
    "Zambia":          {"weo": "ZMB"},
    "Zimbabwe":        {"weo": "ZWE"},
    # ── CIS ───────────────────────────────────────────────────────────────────
    "Russia":          {"weo": "RUS"},
    "Ukraine":         {"weo": "UKR"},
    "Kazakhstan":      {"weo": "KAZ"},
    "Uzbekistan":      {"weo": "UZB"},
}

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────────────
WEO_URL  = "https://www.imf.org/external/datamapper/api/v1"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"

PALETTE = [
    "#38BDF8", "#F97316", "#A3E635", "#E879F9", "#FB7185",
    "#34D399", "#FBBF24", "#818CF8", "#22D3EE", "#F472B6",
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_imf_weo(weo_iso: str) -> tuple[pd.Series, int]:
    """IMF WEO CPI for a single country. Returns (series, last_actual_year)."""
    try:
        r = requests.get(f"{WEO_URL}/PCPIPCH/{weo_iso}", timeout=30)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values", {}).get("PCPIPCH", {}).get(weo_iso, {})
        last_actual = int(
            data.get("info", {}).get("PCPIPCH", {}).get(
                "lastActual", str(datetime.now().year - 1)
            )
        )
        records: dict[pd.Period, float] = {}
        for yr_str, val in vals.items():
            try:
                if val and val not in ("no data", ""):
                    records[pd.Period(yr_str, freq="Y")] = float(val)
            except Exception:
                pass
        s = pd.Series(records, dtype=float)
        if not s.empty:
            s.index = pd.PeriodIndex(s.index, freq="Y")
        return s.sort_index(), last_actual
    except Exception:
        return pd.Series(dtype=float), datetime.now().year - 1


@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_weo_all_countries() -> tuple[pd.DataFrame, int]:
    """
    Fetch CPI for ALL countries in one call.
    Returns (DataFrame: index=iso3, columns=int year, last_actual_year).
    """
    try:
        r = requests.get(f"{WEO_URL}/PCPIPCH", timeout=60)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values", {}).get("PCPIPCH", {})
        last_actual = int(
            data.get("info", {}).get("PCPIPCH", {}).get(
                "lastActual", str(datetime.now().year - 1)
            )
        )
        records: dict[str, dict[int, float]] = {}
        for iso3, yr_dict in vals.items():
            if not isinstance(yr_dict, dict):
                continue
            row: dict[int, float] = {}
            for yr_str, val in yr_dict.items():
                try:
                    if val and val not in ("no data", ""):
                        row[int(yr_str)] = float(val)
                except Exception:
                    pass
            if row:
                records[iso3] = row
        df = pd.DataFrame.from_dict(records, orient="index")
        df.columns = df.columns.astype(int)
        return df.sort_index(axis=1), last_actual
    except Exception:
        return pd.DataFrame(), datetime.now().year - 1


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_fred_annual(series_id: str) -> pd.Series:
    """FRED daily oil price → annual average."""
    try:
        r = requests.get(FRED_URL, params={"id": series_id}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        # Column names vary ("DATE" vs "observation_date") — use positional
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().set_index("date")
        ann = df["value"].resample("YS").mean()
        ann.index = ann.index.to_period("Y")
        return ann.sort_index()
    except Exception:
        return pd.Series(dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def clip_years(s: pd.Series, start: int, end: int) -> pd.Series:
    if s.empty:
        return s
    try:
        ps, pe = pd.Period(start, freq="Y"), pd.Period(end, freq="Y")
        return s[(s.index >= ps) & (s.index <= pe)]
    except Exception:
        return s


def to_dt(s: pd.Series) -> pd.Series:
    s2 = s.copy()
    s2.index = s.index.to_timestamp()
    return s2


def hex_rgba(hex_color: str, alpha: float = 0.1) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


# ─────────────────────────────────────────────────────────────────────────────
# CHART STYLES
# ─────────────────────────────────────────────────────────────────────────────

_BASE_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Inter, system-ui, sans-serif", size=12),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(13,27,42,0.95)",
        bordercolor="rgba(56,189,248,0.3)",
        font_color="#E2E8F0",
        font_size=13,
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#CBD5E1"),
    ),
    xaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        showline=True, linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"),
        zeroline=False,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        showline=True, linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"),
        zeroline=False,
    ),
    margin=dict(l=60, r=40, t=64, b=50),
    height=450,
)

_GEO = dict(
    showframe=False,
    showcoastlines=False,
    projection_type="natural earth",
    bgcolor="rgba(0,0,0,0)",
    landcolor="#1E293B",
    showland=True,
    oceancolor="#0F172A",
    showocean=True,
    lakecolor="#0F172A",
    showlakes=True,
    showcountries=True,
    countrycolor="rgba(255,255,255,0.08)",
)


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_line_chart(
    traces: list[dict],  # [{label, hist, fcast?, unit, color}]
    title: str,
) -> go.Figure:
    units = list(dict.fromkeys(
        t["unit"] for t in traces
        if not t["hist"].empty or not t.get("fcast", pd.Series(dtype=float)).empty
    ))
    dual = len(units) >= 2
    fig  = make_subplots(specs=[[{"secondary_y": True}]]) if dual else go.Figure()
    u1   = units[0] if units else ""
    u2   = units[1] if len(units) > 1 else u1

    def _add(s: pd.Series, name: str, color: str, dash: str,
             unit: str, show_legend: bool = True) -> None:
        if s.empty:
            return
        is_sec = dual and unit != u1
        fill_color = hex_rgba(color, 0.08) if dash == "solid" and not dual else None
        tr = go.Scatter(
            x=to_dt(s).index,
            y=s.values,
            name=name,
            line=dict(color=color, width=2.5, dash=dash),
            mode="lines",
            fill="tozeroy" if fill_color else None,
            fillcolor=fill_color,
            legendgroup=name.split(" (")[0],
            showlegend=show_legend,
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y}}: %{{y:.2f}} {unit}<extra></extra>",
        )
        if dual:
            fig.add_trace(tr, secondary_y=is_sec)
        else:
            fig.add_trace(tr)

    for t in traces:
        fcast = t.get("fcast", pd.Series(dtype=float))
        _add(t["hist"],  t["label"],                t["color"], "solid", t["unit"])
        _add(fcast,      t["label"] + " (forecast)", t["color"], "dot",   t["unit"],
             show_legend=not t["hist"].empty)

    layout = {
        **_BASE_LAYOUT,
        "title": dict(text=title, font=dict(size=14, color="#E2E8F0"), x=0.01),
    }
    fig.update_layout(**layout)

    if dual:
        fig.update_yaxes(title_text=u1, secondary_y=False,
                         title_font=dict(color="#94A3B8", size=11))
        fig.update_yaxes(title_text=u2, secondary_y=True, showgrid=False,
                         title_font=dict(color="#94A3B8", size=11))
    elif units:
        fig.update_yaxes(title_text=u1, title_font=dict(color="#94A3B8", size=11))

    if any("%" in t.get("unit", "") for t in traces):
        fig.add_hline(y=0,  line_dash="dot", line_color="rgba(148,163,184,0.25)", line_width=1)
        fig.add_hline(y=2,  line_dash="dot", line_color="rgba(56,189,248,0.2)",   line_width=1,
                      annotation_text="2%", annotation_font_color="rgba(56,189,248,0.5)",
                      annotation_font_size=10)

    return fig


def build_cpi_world_map(
    df_all: pd.DataFrame,
    year: int,
    last_actual: int,
) -> go.Figure:
    """Choropleth world map for CPI inflation in a given year."""
    if year not in df_all.columns:
        return go.Figure()

    col = df_all[year].dropna()
    is_forecast = year > last_actual
    suffix      = "  ⟡ IMF Forecast" if is_forecast else ""

    fig = go.Figure(go.Choropleth(
        locations=col.index.tolist(),
        z=col.values,
        locationmode="ISO-3",
        colorscale=[
            [0.00, "#0D9488"],   # teal  (deflation / very low)
            [0.20, "#4ADE80"],   # green (~0 %)
            [0.38, "#FEF08A"],   # yellow (~2 % target zone)
            [0.55, "#FB923C"],   # orange (~10 %)
            [0.75, "#EF4444"],   # red   (high inflation)
            [1.00, "#7F1D1D"],   # dark  (hyperinflation)
        ],
        zmin=-5, zmax=30,
        colorbar=dict(
            title=dict(text="CPI %", font=dict(color="#94A3B8", size=12)),
            tickfont=dict(color="#94A3B8", size=11),
            thickness=14, len=0.68,
            bgcolor="rgba(0,0,0,0.45)",
            outlinecolor="rgba(255,255,255,0.08)",
            outlinewidth=1,
        ),
        marker_line_color="rgba(255,255,255,0.12)",
        marker_line_width=0.5,
        hovertemplate="<b>%{location}</b><br>CPI: %{z:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"CPI Inflation — {year}{suffix}",
            font=dict(size=15, color="#E2E8F0"), x=0.01,
        ),
        geo=_GEO,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0),
        height=520,
    )
    return fig


def build_oil_world_map(brent: pd.Series, year: int) -> go.Figure:
    """
    World map shaded uniformly by the global Brent price for a given year,
    conveying that crude oil is a single world-market commodity.
    """
    key = pd.Period(year, freq="Y")
    if key not in brent.index:
        return go.Figure()

    price = float(brent[key])
    # All individual-country ISO-3 codes (skip aggregates like "EURO")
    iso3_all = [v["weo"] for v in COUNTRIES.values() if len(v.get("weo", "")) == 3]

    fig = go.Figure(go.Choropleth(
        locations=iso3_all,
        z=[price] * len(iso3_all),
        locationmode="ISO-3",
        colorscale=[[0, "#92400E"], [0.5, "#EA580C"], [1, "#FCD34D"]],
        zmin=price * 0.9999, zmax=price * 1.0001,
        showscale=False,
        marker_line_color="rgba(255,255,255,0.1)",
        marker_line_width=0.5,
        hovertemplate=f"<b>%{{location}}</b><br>Brent: ${price:.1f} / bbl ({year})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"Brent Crude — World Market Price {year}:  <b>${price:.1f} / bbl</b>",
            font=dict(size=15, color="#E2E8F0"), x=0.01,
        ),
        geo={**_GEO, "landcolor": "#92400E"},
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0),
        height=450,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT APP
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    # ── Gradient header ────────────────────────────────────────────────────────
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(56,189,248,0.07) 0%,
                rgba(99,102,241,0.05) 100%);border:1px solid rgba(56,189,248,0.12);
                border-radius:18px;padding:1.6rem 2rem;margin-bottom:1.4rem;">
      <h1 style="margin:0;font-size:1.85rem;color:#E2E8F0;font-weight:700;
                 letter-spacing:-0.02em;">🌍 Global CPI &amp; Oil Dashboard</h1>
      <p style="margin:0.45rem 0 0;color:rgba(148,163,184,0.75);font-size:0.88rem;">
        Annual inflation · <b style="color:rgba(56,189,248,0.8);">IMF World Economic Outlook</b>
        &nbsp;|&nbsp; Crude oil · <b style="color:rgba(249,115,22,0.8);">FRED</b>
        &nbsp;·&nbsp; Dashed lines = WEO forecast
      </p>
    </div>
    """, unsafe_allow_html=True)

    this_year = datetime.now().year

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️  Settings")

        compare_mode = st.toggle(
            "Multi-country comparison",
            help="Plot one CPI line per country",
        )
        st.markdown("---")

        country_list = sorted(COUNTRIES.keys())
        st.markdown("**Countries**")

        if compare_mode:
            sel_countries = st.multiselect(
                "Countries (up to 10)", country_list,
                default=["United States", "Euro Area", "China", "Brazil", "Nigeria"],
                max_selections=10,
            )
        else:
            sel_country   = st.selectbox(
                "Country", country_list,
                index=country_list.index("United States"),
            )
            sel_countries = [sel_country]

        st.markdown("---")
        st.markdown("**Period**")
        year_opts = list(range(1980, this_year + 7))
        c1, c2    = st.columns(2)
        with c1:
            start_yr = st.selectbox("From", year_opts,
                                    index=year_opts.index(2000),
                                    label_visibility="visible")
        with c2:
            end_yr = st.selectbox("To", year_opts,
                                  index=year_opts.index(min(this_year + 4, year_opts[-1])),
                                  label_visibility="visible")

        st.markdown("---")
        include_forecast = st.toggle("IMF WEO forecasts", value=True)
        fetch_btn = st.button("🔄  Fetch Data", type="primary", use_container_width=True)

    # ── Validate ───────────────────────────────────────────────────────────────
    if not sel_countries:
        st.info("Select at least one country.")
        return
    if start_yr >= end_yr:
        st.error("Start year must be before end year.")
        return

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_map, tab_series, tab_oil = st.tabs([
        "🗺️  World CPI Map",
        "📈  CPI Time Series",
        "🛢️  Oil Price",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — WORLD CPI MAP
    # ─────────────────────────────────────────────────────────────────────────
    with tab_map:
        st.markdown("#### CPI Inflation by Country  ·  IMF WEO")

        with st.spinner("Loading world CPI map…"):
            df_all, last_actual_map = fetch_weo_all_countries()

        if df_all.empty:
            st.warning("Could not load world CPI data from IMF WEO.")
        else:
            map_year = st.slider(
                "Year", min_value=max(start_yr, 1980), max_value=end_yr,
                value=min(this_year, end_yr), step=1,
            )

            fig_map = build_cpi_world_map(df_all, map_year, last_actual_map)
            st.plotly_chart(fig_map, use_container_width=True)

            # Top / bottom tables
            if map_year in df_all.columns:
                col_data = df_all[map_year].dropna().sort_values(ascending=False)
                t1, t2 = st.columns(2)
                with t1:
                    st.markdown("**🔴 Highest inflation**")
                    top = (col_data.head(10)
                                   .reset_index()
                                   .rename(columns={"index": "ISO-3", map_year: "CPI %"}))
                    top["CPI %"] = top["CPI %"].round(1)
                    st.dataframe(top, use_container_width=True,
                                 hide_index=True, height=310)
                with t2:
                    st.markdown("**🟢 Lowest inflation**")
                    bot = (col_data.tail(10).iloc[::-1]
                                   .reset_index()
                                   .rename(columns={"index": "ISO-3", map_year: "CPI %"}))
                    bot["CPI %"] = bot["CPI %"].round(1)
                    st.dataframe(bot, use_container_width=True,
                                 hide_index=True, height=310)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — CPI TIME SERIES
    # ─────────────────────────────────────────────────────────────────────────
    with tab_series:
        fetch_key = (tuple(sorted(sel_countries)), start_yr, end_yr, include_forecast)
        if "ts_cache" not in st.session_state:
            st.session_state.ts_cache = {}
            st.session_state.ts_key   = None

        if fetch_btn or st.session_state.ts_key != fetch_key:
            st.session_state.ts_key = fetch_key
            cache: dict[str, tuple] = {}
            prog = st.progress(0, text="Fetching CPI data…")
            for i, country in enumerate(sel_countries):
                prog.progress(i / len(sel_countries), text=f"Loading {country}…")
                weo_iso = COUNTRIES[country].get("weo")
                if weo_iso:
                    ann, last_act = fetch_imf_weo(weo_iso)
                    if not ann.empty:
                        cut   = pd.Period(last_act, freq="Y")
                        hist  = clip_years(ann[ann.index <= cut], start_yr, end_yr)
                        fcast = (
                            clip_years(ann[ann.index > cut], start_yr, end_yr)
                            if include_forecast else pd.Series(dtype=float)
                        )
                        cache[country] = (hist, fcast, last_act)
                    else:
                        cache[country] = (pd.Series(dtype=float),
                                          pd.Series(dtype=float), this_year - 1)
            prog.empty()
            st.session_state.ts_cache = cache

        ts = st.session_state.ts_cache

        if compare_mode:
            # ── Multi-country: one chart ────────────────────────────────────
            traces = []
            for i, country in enumerate(sel_countries):
                if country in ts:
                    h, f, _ = ts[country]
                    if not h.empty or not f.empty:
                        traces.append({
                            "label": country, "hist": h, "fcast": f,
                            "unit": "%", "color": PALETTE[i % len(PALETTE)],
                        })
            if traces:
                st.plotly_chart(
                    build_line_chart(traces, "CPI Inflation (YoY %) — Country Comparison"),
                    use_container_width=True,
                )
            else:
                st.info("No data — click **Fetch Data**.")

        else:
            # ── Single-country ──────────────────────────────────────────────
            country = sel_countries[0]
            if country in ts:
                h, f, last_act = ts[country]
                full = pd.concat([h, f]).dropna().sort_index()

                if not full.empty:
                    latest  = full.iloc[-1]
                    delta   = (full.iloc[-1] - full.iloc[-2]) if len(full) >= 2 else None
                    peak_v  = full.max()
                    trough_v = full.min()

                    m1, m2, m3 = st.columns(3)
                    m1.metric(
                        f"Latest CPI — {full.index[-1]}",
                        f"{latest:.2f} %",
                        f"{delta:+.2f} pp vs prev. year" if delta is not None else None,
                    )
                    m2.metric("Peak", f"{peak_v:.2f} %", str(full.idxmax()))
                    m3.metric("Trough", f"{trough_v:.2f} %", str(full.idxmin()))
                    st.markdown("")

                if not h.empty or not f.empty:
                    st.plotly_chart(
                        build_line_chart(
                            [{"label": f"CPI — {country}", "hist": h, "fcast": f,
                              "unit": "%", "color": PALETTE[0]}],
                            f"CPI Inflation (YoY %) — {country}  ·  IMF WEO",
                        ),
                        use_container_width=True,
                    )
            else:
                st.info("No data — click **Fetch Data**.")

        # ── Data table ─────────────────────────────────────────────────────────
        if ts:
            with st.expander("📋 Data table & Download"):
                frames = []
                for cname, (h, f, _) in ts.items():
                    full = pd.concat([h, f]).sort_index()
                    if not full.empty:
                        df_tmp = full.rename(cname).to_frame()
                        df_tmp.index = [str(p) for p in df_tmp.index]
                        frames.append(df_tmp)
                if frames:
                    combined = pd.concat(frames, axis=1).sort_index(ascending=False).round(3)
                    st.dataframe(combined, use_container_width=True, height=320)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.download_button(
                            "⬇️  CSV", combined.to_csv(),
                            "cpi_data.csv", "text/csv",
                            use_container_width=True,
                        )
                    with cc2:
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine="openpyxl") as w:
                            combined.to_excel(w, sheet_name="CPI")
                        st.download_button(
                            "⬇️  Excel", buf.getvalue(), "cpi_data.xlsx",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — OIL PRICE
    # ─────────────────────────────────────────────────────────────────────────
    with tab_oil:
        st.markdown("#### Crude Oil — Global Benchmark Prices  ·  FRED")

        with st.spinner("Loading oil prices…"):
            brent = clip_years(fetch_fred_annual("DCOILBRENTEU"), start_yr, end_yr)
            wti   = clip_years(fetch_fred_annual("DCOILWTICO"),   start_yr, end_yr)

        if brent.empty and wti.empty:
            st.warning("Could not load oil price data from FRED.")
        else:
            # ── KPI cards ────────────────────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            if not brent.empty:
                bl = brent.iloc[-1]
                bd = (brent.iloc[-1] - brent.iloc[-2]) if len(brent) >= 2 else None
                m1.metric(f"Brent (latest · {brent.index[-1]})",
                          f"${bl:.1f} / bbl",
                          f"{bd:+.1f}" if bd is not None else None)
                m2.metric("Brent peak", f"${brent.max():.1f} / bbl",
                          str(brent.idxmax()))
            if not wti.empty:
                wl = wti.iloc[-1]
                wd = (wti.iloc[-1] - wti.iloc[-2]) if len(wti) >= 2 else None
                m3.metric(f"WTI (latest · {wti.index[-1]})",
                          f"${wl:.1f} / bbl",
                          f"{wd:+.1f}" if wd is not None else None)
                m4.metric("WTI peak", f"${wti.max():.1f} / bbl",
                          str(wti.idxmax()))

            st.markdown("")

            # ── Line chart ───────────────────────────────────────────────────
            traces_oil = []
            if not brent.empty:
                traces_oil.append({"label": "Brent Crude",
                                   "hist": brent, "unit": "USD/bbl",
                                   "color": PALETTE[1]})
            if not wti.empty:
                traces_oil.append({"label": "WTI Crude",
                                   "hist": wti, "unit": "USD/bbl",
                                   "color": PALETTE[0]})
            if traces_oil:
                st.plotly_chart(
                    build_line_chart(traces_oil, "Crude Oil Prices — Annual Average"),
                    use_container_width=True,
                )

            # ── World map ────────────────────────────────────────────────────
            st.markdown("---")
            st.markdown("#### 🌍 Oil Price World Map")
            st.caption("Global Brent crude price for the selected year — "
                       "one world market, one price.")

            oil_years = [int(str(p)) for p in brent.index
                         if start_yr <= int(str(p)) <= end_yr]
            if oil_years:
                oil_map_yr = st.slider(
                    "Year", min_value=oil_years[0], max_value=oil_years[-1],
                    value=min(this_year, oil_years[-1]), step=1,
                    key="oil_map_yr",
                )
                fig_oil_map = build_oil_world_map(brent, oil_map_yr)
                st.plotly_chart(fig_oil_map, use_container_width=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem;color:rgba(100,116,139,0.7);text-align:center'>"
        "CPI data · <b>IMF World Economic Outlook</b> (PCPIPCH, annual) — "
        "Oil prices · <b>FRED</b> (Brent DCOILBRENTEU, WTI DCOILWTICO, daily → annual avg)"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
