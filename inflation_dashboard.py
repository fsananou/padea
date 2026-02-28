#!/usr/bin/env python3
"""
Data Board — Macro & Financial Reference Data for Accounting Professionals
Sources: IMF WEO · FRED · Yahoo Finance
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
    page_title="Data Board",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main {
    background: linear-gradient(160deg, #07101f 0%, #0c1a2e 60%, #07101f 100%);
}
[data-testid="stSidebar"] > div:first-child {
    background: linear-gradient(180deg, #0b1726 0%, #0e2038 100%);
    border-right: 1px solid rgba(56,189,248,0.1);
}
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span {
    color: rgba(226,232,240,0.85) !important;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 5px; background: rgba(255,255,255,0.025);
    border-radius: 14px; padding: 5px;
    border: 1px solid rgba(56,189,248,0.1);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px; padding: 7px 16px;
    color: rgba(226,232,240,0.45); font-weight: 500;
    font-size: 0.87rem; letter-spacing: 0.02em;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg,rgba(56,189,248,0.18),rgba(99,102,241,0.14)) !important;
    color: #38BDF8 !important;
    border: 1px solid rgba(56,189,248,0.28) !important;
}
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(56,189,248,0.12);
    border-radius: 16px; padding: 1rem 1.3rem;
}
[data-testid="stMetric"] label {
    color: rgba(148,163,184,0.85) !important;
    font-size: 0.72rem !important;
    text-transform: uppercase; letter-spacing: 0.08em;
}
[data-testid="stMetricValue"] {
    color: #38BDF8 !important; font-size: 1.75rem !important; font-weight: 700 !important;
}
hr { border-color: rgba(56,189,248,0.1) !important; }
h1, h2, h3, h4 { color: #e2e8f0 !important; }
p, li { color: rgba(226,232,240,0.7) !important; }
.block-container { padding-top: 1.6rem; padding-bottom: 2rem; }
[data-testid="stExpander"] {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(56,189,248,0.1) !important;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY CATALOG
# ─────────────────────────────────────────────────────────────────────────────
COUNTRIES: dict[str, dict] = {
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
    "Poland":          {"weo": "POL"},
    "Czech Republic":  {"weo": "CZE"},
    "Hungary":         {"weo": "HUN"},
    "Romania":         {"weo": "ROU"},
    "Bulgaria":        {"weo": "BGR"},
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
    "Russia":          {"weo": "RUS"},
    "Ukraine":         {"weo": "UKR"},
    "Kazakhstan":      {"weo": "KAZ"},
    "Uzbekistan":      {"weo": "UZB"},
}

# ─────────────────────────────────────────────────────────────────────────────
# WORLD MAP INDICATOR CONFIG
# ─────────────────────────────────────────────────────────────────────────────
MAP_INDICATORS: dict[str, dict] = {
    "CPI Inflation (%)": {
        "weo_code": "PCPIPCH",
        "colorscale": [
            [0.00, "#0D9488"], [0.20, "#4ADE80"], [0.38, "#FEF08A"],
            [0.55, "#FB923C"], [0.75, "#EF4444"], [1.00, "#7F1D1D"],
        ],
        "zmin": -5, "zmax": 30, "unit": "%",
    },
    "Real GDP Growth (%)": {
        "weo_code": "NGDP_RPCH",
        "colorscale": [
            [0.00, "#7F1D1D"], [0.22, "#EF4444"], [0.40, "#FEF08A"],
            [0.52, "#86EFAC"], [0.72, "#22C55E"], [1.00, "#14532D"],
        ],
        "zmin": -15, "zmax": 15, "unit": "%",
    },
    "Unemployment Rate (%)": {
        "weo_code": "LUR",
        "colorscale": [
            [0.00, "#F0FDF4"], [0.25, "#86EFAC"],
            [0.55, "#F97316"], [1.00, "#7F1D1D"],
        ],
        "zmin": 0, "zmax": 30, "unit": "%",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# FRED SERIES
# ─────────────────────────────────────────────────────────────────────────────
POLICY_SERIES: dict[str, str] = {
    "Fed Funds Rate":     "FEDFUNDS",        # US policy rate
    "ECB Deposit Rate":   "ECBDFR",          # ECB deposit facility rate
    "3M USD LIBOR":       "USD3MTD156N",      # 3-month USD interbank
    "3M EURIBOR":         "EUR3MTD156N",      # 3-month EUR interbank
}
YIELD_SERIES: dict[str, str] = {
    "US 10Y Treasury":    "GS10",
    "Euro Area 10Y":      "IRLTLT01EZM156N",
    "UK 10Y Gilt":        "IRLTLT01GBM156N",
    "Japan 10Y Bond":     "IRLTLT01JPM156N",
}
SPREAD_SERIES: dict[str, str] = {
    "US IG Corp OAS":     "BAMLC0A0CM",
    "US HY Corp OAS":     "BAMLH0A0HYM2",
    "Euro HY OAS":        "BAMLHE00EHY0EY",
}
FX_SERIES: dict[str, str] = {
    "EUR / USD":          "DEXUSEU",   # USD per 1 EUR
    "GBP / USD":          "DEXUSUK",   # USD per 1 GBP
    "JPY / USD":          "DEXJPUS",   # JPY per 1 USD
    "CNY / USD":          "DEXCHUS",   # CNY per 1 USD
}

# ─────────────────────────────────────────────────────────────────────────────
# EQUITY INDICES (Yahoo Finance)
# ─────────────────────────────────────────────────────────────────────────────
EQUITY_TICKERS: dict[str, str] = {
    "S&P 500":       "^GSPC",
    "CAC 40":        "^FCHI",
    "Euro Stoxx 50": "^STOXX50E",
    "Nikkei 225":    "^N225",
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
def fetch_weo_series(weo_code: str, weo_iso: str) -> tuple[pd.Series, int]:
    """IMF WEO: any indicator for a single country. Returns (series, last_actual_year)."""
    try:
        r = requests.get(f"{WEO_URL}/{weo_code}/{weo_iso}", timeout=30)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values", {}).get(weo_code, {}).get(weo_iso, {})
        last_actual = int(
            data.get("info", {}).get(weo_code, {}).get(
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
def fetch_weo_world(weo_code: str) -> tuple[pd.DataFrame, int]:
    """IMF WEO: any indicator for ALL countries. Returns (df, last_actual_year)."""
    try:
        r = requests.get(f"{WEO_URL}/{weo_code}", timeout=60)
        r.raise_for_status()
        data = r.json()
        vals = data.get("values", {}).get(weo_code, {})
        last_actual = int(
            data.get("info", {}).get(weo_code, {}).get(
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
    """FRED: any series → annual average."""
    try:
        r = requests.get(FRED_URL, params={"id": series_id}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text))
        df.columns = ["date", "value"]
        df["date"]  = pd.to_datetime(df["date"], errors="coerce")
        df["value"] = pd.to_numeric(df["value"], errors="coerce")
        df = df.dropna().set_index("date")
        ann = df["value"].resample("YS").mean()
        ann.index = ann.index.to_period("Y")
        return ann.sort_index()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_yahoo_annual(ticker: str) -> pd.Series:
    """Yahoo Finance: equity index → annual average of monthly closes."""
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        r = requests.get(
            url,
            params={"interval": "1mo", "range": "40y"},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=30,
        )
        r.raise_for_status()
        result = r.json()["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes     = result["indicators"]["adjclose"][0]["adjclose"]
        df = pd.DataFrame({
            "date":  pd.to_datetime(timestamps, unit="s"),
            "value": closes,
        }).dropna().set_index("date")
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
# SHARED CHART STYLES
# ─────────────────────────────────────────────────────────────────────────────

_BASE_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#94A3B8", family="Inter, system-ui, sans-serif", size=12),
    hovermode="x unified",
    hoverlabel=dict(
        bgcolor="rgba(13,27,42,0.95)",
        bordercolor="rgba(56,189,248,0.3)",
        font_color="#E2E8F0", font_size=13,
    ),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(0,0,0,0)", font=dict(size=11, color="#CBD5E1"),
    ),
    xaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        showline=True, linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"), zeroline=False,
    ),
    yaxis=dict(
        showgrid=True, gridcolor="rgba(255,255,255,0.04)",
        showline=True, linecolor="rgba(255,255,255,0.08)",
        tickfont=dict(color="#64748B"), zeroline=False,
    ),
    margin=dict(l=60, r=40, t=60, b=50),
    height=420,
)

_GEO = dict(
    showframe=False, showcoastlines=False,
    projection_type="natural earth",
    bgcolor="rgba(0,0,0,0)",
    landcolor="#1E293B", showland=True,
    oceancolor="#0F172A", showocean=True,
    lakecolor="#0F172A", showlakes=True,
    showcountries=True, countrycolor="rgba(255,255,255,0.08)",
)


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def build_line_chart(
    traces: list[dict],
    title:  str,
    hline_zero: bool = False,
    hline_2:    bool = False,
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
        is_sec  = dual and unit != u1
        fill_c  = hex_rgba(color, 0.07) if dash == "solid" and not dual else None
        tr = go.Scatter(
            x=to_dt(s).index, y=s.values, name=name,
            line=dict(color=color, width=2.5, dash=dash),
            mode="lines",
            fill="tozeroy" if fill_c else None,
            fillcolor=fill_c,
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

    fig.update_layout(
        **_BASE_LAYOUT,
        title=dict(text=title, font=dict(size=14, color="#E2E8F0"), x=0.01),
    )
    if dual:
        fig.update_yaxes(title_text=u1, secondary_y=False,
                         title_font=dict(color="#94A3B8", size=11))
        fig.update_yaxes(title_text=u2, secondary_y=True, showgrid=False,
                         title_font=dict(color="#94A3B8", size=11))
    elif units:
        fig.update_yaxes(title_text=u1, title_font=dict(color="#94A3B8", size=11))
    if hline_zero:
        fig.add_hline(y=0, line_dash="dot",
                      line_color="rgba(148,163,184,0.25)", line_width=1)
    if hline_2:
        fig.add_hline(y=2, line_dash="dot",
                      line_color="rgba(56,189,248,0.2)", line_width=1,
                      annotation_text="2%",
                      annotation_font_color="rgba(56,189,248,0.5)",
                      annotation_font_size=10)
    return fig


def build_world_map(
    df_all:       pd.DataFrame,
    year:         int,
    last_actual:  int,
    ind_name:     str,
    ind_cfg:      dict,
) -> go.Figure:
    if year not in df_all.columns:
        return go.Figure()
    col     = df_all[year].dropna()
    suffix  = "  ⟡ IMF Forecast" if year > last_actual else ""
    fig = go.Figure(go.Choropleth(
        locations=col.index.tolist(),
        z=col.values,
        locationmode="ISO-3",
        colorscale=ind_cfg["colorscale"],
        zmin=ind_cfg["zmin"], zmax=ind_cfg["zmax"],
        colorbar=dict(
            title=dict(text=ind_cfg["unit"], font=dict(color="#94A3B8", size=12)),
            tickfont=dict(color="#94A3B8", size=11),
            thickness=14, len=0.68,
            bgcolor="rgba(0,0,0,0.45)",
            outlinecolor="rgba(255,255,255,0.08)", outlinewidth=1,
        ),
        marker_line_color="rgba(255,255,255,0.12)",
        marker_line_width=0.5,
        hovertemplate=(
            f"<b>%{{location}}</b><br>{ind_name}: "
            f"%{{z:.1f}} {ind_cfg['unit']}<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=dict(text=f"{ind_name} — {year}{suffix}",
                   font=dict(size=15, color="#E2E8F0"), x=0.01),
        geo=_GEO,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0), height=520,
    )
    return fig


def build_oil_world_map(brent: pd.Series, year: int) -> go.Figure:
    key = pd.Period(year, freq="Y")
    if key not in brent.index:
        return go.Figure()
    price    = float(brent[key])
    iso3_all = [v["weo"] for v in COUNTRIES.values() if len(v.get("weo", "")) == 3]
    fig = go.Figure(go.Choropleth(
        locations=iso3_all, z=[price] * len(iso3_all),
        locationmode="ISO-3",
        colorscale=[[0, "#92400E"], [0.5, "#EA580C"], [1, "#FCD34D"]],
        zmin=price * 0.9999, zmax=price * 1.0001,
        showscale=False,
        marker_line_color="rgba(255,255,255,0.1)", marker_line_width=0.5,
        hovertemplate=(
            f"<b>%{{location}}</b><br>Brent: ${price:.1f}/bbl ({year})<extra></extra>"
        ),
    ))
    fig.update_layout(
        title=dict(
            text=f"Brent Crude — World Market Price {year}:  <b>${price:.1f} / bbl</b>",
            font=dict(size=15, color="#E2E8F0"), x=0.01,
        ),
        geo={**_GEO, "landcolor": "#92400E"},
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=50, b=0), height=450,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(56,189,248,0.07) 0%,
                rgba(99,102,241,0.05) 100%);border:1px solid rgba(56,189,248,0.12);
                border-radius:18px;padding:1.6rem 2rem;margin-bottom:1.4rem;">
      <h1 style="margin:0;font-size:1.85rem;color:#E2E8F0;font-weight:700;
                 letter-spacing:-0.02em;">📊 Data Board</h1>
      <p style="margin:0.45rem 0 0;color:rgba(148,163,184,0.75);font-size:0.88rem;">
        Macro &amp; Financial Reference Data for Accounting Professionals &nbsp;·&nbsp;
        <b style="color:rgba(56,189,248,0.8);">IMF WEO</b> &nbsp;·&nbsp;
        <b style="color:rgba(249,115,22,0.8);">FRED</b> &nbsp;·&nbsp;
        <b style="color:rgba(163,230,53,0.8);">Yahoo Finance</b>
      </p>
    </div>
    """, unsafe_allow_html=True)

    this_year = datetime.now().year

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️  Settings")
        compare_mode = st.toggle(
            "Multi-country comparison",
            help="Plot one line per country on Macro tab",
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
            start_yr = st.selectbox("From", year_opts, index=year_opts.index(2000))
        with c2:
            end_yr   = st.selectbox("To",   year_opts,
                                    index=year_opts.index(min(this_year + 4, year_opts[-1])))

        st.markdown("---")
        include_forecast = st.toggle("IMF WEO forecasts", value=True)
        fetch_btn = st.button("🔄  Fetch Data", type="primary", use_container_width=True)

    if not sel_countries:
        st.info("Select at least one country.")
        return
    if start_yr >= end_yr:
        st.error("Start year must be before end year.")
        return

    # ── Tabs ───────────────────────────────────────────────────────────────────
    tab_map, tab_macro, tab_rates, tab_fx, tab_mkt = st.tabs([
        "🗺️  World Map",
        "📈  Macro",
        "💰  Rates & Credit",
        "💱  FX & Oil",
        "📊  Markets",
    ])

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 1 — WORLD MAP
    # ─────────────────────────────────────────────────────────────────────────
    with tab_map:
        ind_name = st.selectbox(
            "Indicator", list(MAP_INDICATORS.keys()), key="map_ind",
        )
        ind_cfg = MAP_INDICATORS[ind_name]

        with st.spinner(f"Loading {ind_name} world map…"):
            df_all, last_actual_map = fetch_weo_world(ind_cfg["weo_code"])

        if df_all.empty:
            st.warning("Could not load data from IMF WEO.")
        else:
            map_year = st.slider(
                "Year", min_value=max(start_yr, 1980), max_value=end_yr,
                value=min(this_year, end_yr), step=1,
            )
            st.plotly_chart(
                build_world_map(df_all, map_year, last_actual_map, ind_name, ind_cfg),
                use_container_width=True,
            )
            if map_year in df_all.columns:
                col_data = df_all[map_year].dropna().sort_values(ascending=False)
                t1, t2   = st.columns(2)
                with t1:
                    st.markdown("**🔴 Highest**")
                    top = (col_data.head(10).reset_index()
                                   .rename(columns={"index": "ISO-3", map_year: ind_cfg["unit"]}))
                    top[ind_cfg["unit"]] = top[ind_cfg["unit"]].round(1)
                    st.dataframe(top, use_container_width=True, hide_index=True, height=310)
                with t2:
                    st.markdown("**🟢 Lowest**")
                    bot = (col_data.tail(10).iloc[::-1].reset_index()
                                   .rename(columns={"index": "ISO-3", map_year: ind_cfg["unit"]}))
                    bot[ind_cfg["unit"]] = bot[ind_cfg["unit"]].round(1)
                    st.dataframe(bot, use_container_width=True, hide_index=True, height=310)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 2 — MACRO (CPI · GDP · Unemployment)
    # ─────────────────────────────────────────────────────────────────────────
    with tab_macro:
        fetch_key = (tuple(sorted(sel_countries)), start_yr, end_yr, include_forecast)
        if "macro_cache" not in st.session_state:
            st.session_state.macro_cache = {}
            st.session_state.macro_key   = None

        if fetch_btn or st.session_state.macro_key != fetch_key:
            st.session_state.macro_key = fetch_key
            cache: dict[str, dict] = {}
            weo_tasks = [
                ("PCPIPCH", "cpi",   "CPI"),
                ("NGDP_RPCH", "gdp", "GDP Growth"),
                ("LUR",    "unemp",  "Unemployment"),
            ]
            n_total = len(sel_countries) * len(weo_tasks)
            prog    = st.progress(0, text="Fetching macro data…")
            step    = 0
            for country in sel_countries:
                weo_iso = COUNTRIES[country].get("weo")
                cd: dict[str, tuple] = {}
                for weo_code, key, label in weo_tasks:
                    prog.progress(step / n_total, text=f"{country} — {label}…")
                    if weo_iso:
                        ann, last_act = fetch_weo_series(weo_code, weo_iso)
                        if not ann.empty:
                            cut   = pd.Period(last_act, freq="Y")
                            hist  = clip_years(ann[ann.index <= cut], start_yr, end_yr)
                            fcast = (
                                clip_years(ann[ann.index > cut], start_yr, end_yr)
                                if include_forecast else pd.Series(dtype=float)
                            )
                            cd[key] = (hist, fcast, last_act)
                        else:
                            cd[key] = (pd.Series(dtype=float),
                                       pd.Series(dtype=float), this_year - 1)
                    step += 1
                cache[country] = cd
            prog.empty()
            st.session_state.macro_cache = cache

        macro = st.session_state.macro_cache

        ind_tabs = st.tabs(["📈 CPI Inflation", "📊 GDP Growth", "👷 Unemployment"])
        ind_meta = [
            ("cpi",   "CPI Inflation (YoY %)", "%", True,  True),
            ("gdp",   "Real GDP Growth (%)",   "%", True,  False),
            ("unemp", "Unemployment Rate (%)", "%", False, False),
        ]

        for i_tab, (key, label, unit, hl0, hl2) in enumerate(ind_meta):
            with ind_tabs[i_tab]:
                if compare_mode:
                    traces = []
                    for i_c, country in enumerate(sel_countries):
                        if country in macro and key in macro[country]:
                            h, f, _ = macro[country][key]
                            if not h.empty or not f.empty:
                                traces.append({
                                    "label": country, "hist": h, "fcast": f,
                                    "unit": unit, "color": PALETTE[i_c % len(PALETTE)],
                                })
                    if traces:
                        st.plotly_chart(
                            build_line_chart(traces, f"{label} — Comparison",
                                             hline_zero=hl0, hline_2=hl2),
                            use_container_width=True,
                        )
                    else:
                        st.info("No data — click **Fetch Data**.")
                else:
                    country = sel_countries[0]
                    if country in macro and key in macro[country]:
                        h, f, _ = macro[country][key]
                        full = pd.concat([h, f]).dropna().sort_index()
                        if not full.empty:
                            m1, m2, m3 = st.columns(3)
                            latest = full.iloc[-1]
                            delta  = (full.iloc[-1] - full.iloc[-2]) if len(full) >= 2 else None
                            m1.metric(f"Latest  ({full.index[-1]})",
                                      f"{latest:.2f} %",
                                      f"{delta:+.2f} pp" if delta is not None else None)
                            m2.metric("Peak",   f"{full.max():.2f} %", str(full.idxmax()))
                            m3.metric("Trough", f"{full.min():.2f} %", str(full.idxmin()))
                            st.markdown("")
                        if not h.empty or not f.empty:
                            st.plotly_chart(
                                build_line_chart(
                                    [{"label": f"{label} — {country}",
                                      "hist": h, "fcast": f,
                                      "unit": unit, "color": PALETTE[0]}],
                                    f"{label} — {country}  ·  IMF WEO",
                                    hline_zero=hl0, hline_2=hl2,
                                ),
                                use_container_width=True,
                            )
                    else:
                        st.info("No data — click **Fetch Data**.")

        if macro:
            with st.expander("📋 Data & Download"):
                frames = []
                for country, cd in macro.items():
                    for key, (h, f, _) in cd.items():
                        full = pd.concat([h, f]).sort_index()
                        if not full.empty:
                            col_name = f"{country} — {key.upper()}"
                            df_tmp = full.rename(col_name).to_frame()
                            df_tmp.index = [str(p) for p in df_tmp.index]
                            frames.append(df_tmp)
                if frames:
                    combined = pd.concat(frames, axis=1).sort_index(ascending=False).round(3)
                    st.dataframe(combined, use_container_width=True, height=300)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        st.download_button("⬇️ CSV", combined.to_csv(),
                                           "macro_data.csv", "text/csv",
                                           use_container_width=True)
                    with cc2:
                        buf = io.BytesIO()
                        with pd.ExcelWriter(buf, engine="openpyxl") as w:
                            combined.to_excel(w, sheet_name="Macro")
                        st.download_button("⬇️ Excel", buf.getvalue(), "macro_data.xlsx",
                                           "application/vnd.openxmlformats-officedocument"
                                           ".spreadsheetml.sheet",
                                           use_container_width=True)

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 3 — RATES & CREDIT
    # ─────────────────────────────────────────────────────────────────────────
    with tab_rates:
        r1, r2, r3 = st.tabs([
            "🏦 Policy & Interbank",
            "📐 Gov't Bond Yields",
            "📉 Credit Spreads",
        ])

        with r1:
            st.markdown("#### Central Bank Policy Rates & Interbank Benchmarks")
            st.caption("Annual average · FRED")
            traces = []
            for i, (name, sid) in enumerate(POLICY_SERIES.items()):
                s = clip_years(fetch_fred_annual(sid), start_yr, end_yr)
                if not s.empty:
                    traces.append({"label": name, "hist": s,
                                   "unit": "%", "color": PALETTE[i]})
            if traces:
                st.plotly_chart(
                    build_line_chart(traces, "Policy & Interbank Rates — Annual Average",
                                     hline_zero=True),
                    use_container_width=True,
                )
            else:
                st.warning("Could not load rate data from FRED.")

        with r2:
            st.markdown("#### 10-Year Government Bond Yields")
            st.caption("Risk-free rate proxy · used in IFRS 36 DCF, IAS 19 pensions, IFRS 16 leases · FRED")
            traces = []
            for i, (name, sid) in enumerate(YIELD_SERIES.items()):
                s = clip_years(fetch_fred_annual(sid), start_yr, end_yr)
                if not s.empty:
                    traces.append({"label": name, "hist": s,
                                   "unit": "%", "color": PALETTE[i]})
            if traces:
                st.plotly_chart(
                    build_line_chart(traces, "10Y Government Bond Yields — Annual Average",
                                     hline_zero=True),
                    use_container_width=True,
                )
            else:
                st.warning("Could not load yield data from FRED.")

        with r3:
            st.markdown("#### Corporate Bond Spreads — Option-Adjusted Spread (OAS)")
            st.caption(
                "Higher OAS = more credit risk · Used in cost of capital, impairment (IAS 36), "
                "and fair value measurement · FRED / ICE BofA"
            )
            traces = []
            for i, (name, sid) in enumerate(SPREAD_SERIES.items()):
                s = clip_years(fetch_fred_annual(sid), start_yr, end_yr)
                if not s.empty:
                    traces.append({"label": name, "hist": s,
                                   "unit": "bps", "color": PALETTE[i]})
            if traces:
                st.plotly_chart(
                    build_line_chart(traces, "Corporate Bond Spreads (OAS bps) — Annual Average"),
                    use_container_width=True,
                )
            else:
                st.warning("Could not load spread data from FRED.")

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 4 — FX & OIL
    # ─────────────────────────────────────────────────────────────────────────
    with tab_fx:
        fx1, fx2 = st.tabs(["💱 Exchange Rates", "🛢️ Oil Price"])

        with fx1:
            st.markdown("#### Major Exchange Rates — Annual Averages")
            st.caption("IAS 21 foreign currency translation reference · FRED")
            traces = []
            for i, (name, sid) in enumerate(FX_SERIES.items()):
                s = clip_years(fetch_fred_annual(sid), start_yr, end_yr)
                if not s.empty:
                    traces.append({"label": name, "hist": s,
                                   "unit": "rate", "color": PALETTE[i]})
            if traces:
                st.plotly_chart(
                    build_line_chart(traces, "Exchange Rates — Annual Average"),
                    use_container_width=True,
                )
                st.caption(
                    "EUR/USD & GBP/USD: USD per 1 unit of foreign currency "
                    "(higher = stronger EUR/GBP).  "
                    "JPY/USD & CNY/USD: units per 1 USD (higher = weaker local currency)."
                )
            else:
                st.warning("Could not load FX data from FRED.")

        with fx2:
            st.markdown("#### Crude Oil — Global Benchmark Prices")
            brent = clip_years(fetch_fred_annual("DCOILBRENTEU"), start_yr, end_yr)
            wti   = clip_years(fetch_fred_annual("DCOILWTICO"),   start_yr, end_yr)

            if brent.empty and wti.empty:
                st.warning("Could not load oil data from FRED.")
            else:
                m1, m2, m3, m4 = st.columns(4)
                if not brent.empty:
                    bl = brent.iloc[-1]
                    bd = (brent.iloc[-1] - brent.iloc[-2]) if len(brent) >= 2 else None
                    m1.metric(f"Brent · {brent.index[-1]}",
                              f"${bl:.1f} / bbl",
                              f"{bd:+.1f}" if bd is not None else None)
                    m2.metric("Brent peak", f"${brent.max():.1f} / bbl",
                              str(brent.idxmax()))
                if not wti.empty:
                    wl = wti.iloc[-1]
                    wd = (wti.iloc[-1] - wti.iloc[-2]) if len(wti) >= 2 else None
                    m3.metric(f"WTI · {wti.index[-1]}",
                              f"${wl:.1f} / bbl",
                              f"{wd:+.1f}" if wd is not None else None)
                    m4.metric("WTI peak", f"${wti.max():.1f} / bbl",
                              str(wti.idxmax()))

                oil_traces = []
                if not brent.empty:
                    oil_traces.append({"label": "Brent Crude",
                                       "hist": brent, "unit": "USD/bbl",
                                       "color": PALETTE[1]})
                if not wti.empty:
                    oil_traces.append({"label": "WTI Crude",
                                       "hist": wti, "unit": "USD/bbl",
                                       "color": PALETTE[0]})
                if oil_traces:
                    st.plotly_chart(
                        build_line_chart(oil_traces, "Crude Oil Prices — Annual Average"),
                        use_container_width=True,
                    )
                st.markdown("---")
                st.markdown("#### 🌍 Oil Price World Map")
                if not brent.empty:
                    oil_years = [int(str(p)) for p in brent.index
                                 if start_yr <= int(str(p)) <= end_yr]
                    if oil_years:
                        oil_yr = st.slider(
                            "Year", min_value=oil_years[0], max_value=oil_years[-1],
                            value=min(this_year, oil_years[-1]), step=1, key="oil_yr",
                        )
                        st.plotly_chart(
                            build_oil_world_map(brent, oil_yr),
                            use_container_width=True,
                        )

    # ─────────────────────────────────────────────────────────────────────────
    # TAB 5 — MARKETS
    # ─────────────────────────────────────────────────────────────────────────
    with tab_mkt:
        st.markdown("#### Equity Market Indices")
        st.caption("Annual average of monthly close prices · Yahoo Finance")

        with st.spinner("Loading market data…"):
            raw_traces = []
            for i, (name, ticker) in enumerate(EQUITY_TICKERS.items()):
                s = clip_years(fetch_yahoo_annual(ticker), start_yr, end_yr)
                if not s.empty:
                    raw_traces.append({
                        "label": name, "hist": s,
                        "unit": "Index", "color": PALETTE[i],
                    })

        if not raw_traces:
            st.warning("Could not load market data from Yahoo Finance.")
        else:
            # KPI: latest level + YoY
            cols = st.columns(len(raw_traces))
            for col, t in zip(cols, raw_traces):
                s = t["hist"]
                latest = s.iloc[-1]
                delta  = (s.iloc[-1] / s.iloc[-2] - 1) * 100 if len(s) >= 2 else None
                col.metric(
                    f"{t['label']} · {s.index[-1]}",
                    f"{latest:,.0f}",
                    f"{delta:+.1f} %" if delta is not None else None,
                )
            st.markdown("")

            # Level + rebased
            norm_traces = []
            for t in raw_traces:
                s    = t["hist"]
                base = s.iloc[0]
                norm_traces.append({**t, "hist": s / base * 100, "unit": "Index (100=start)"})

            col_l, col_r = st.columns(2)
            with col_l:
                st.plotly_chart(
                    build_line_chart(raw_traces, "Equity Indices — Level"),
                    use_container_width=True,
                )
            with col_r:
                st.plotly_chart(
                    build_line_chart(norm_traces, f"Rebased to 100  (base = {start_yr})"),
                    use_container_width=True,
                )

            # YoY returns
            yoy_traces = []
            for t in raw_traces:
                s = t["hist"]
                if len(s) >= 2:
                    yoy = (s.pct_change(1) * 100).dropna()
                    yoy_traces.append({
                        **t, "hist": yoy, "unit": "%",
                    })
            if yoy_traces:
                st.plotly_chart(
                    build_line_chart(yoy_traces, "Equity Index Returns (YoY %)",
                                     hline_zero=True),
                    use_container_width=True,
                )

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<p style='font-size:0.78rem;color:rgba(100,116,139,0.65);text-align:center'>"
        "Macro: <b>IMF World Economic Outlook</b> (CPI PCPIPCH · GDP NGDP_RPCH · "
        "Unemployment LUR) &nbsp;·&nbsp; "
        "Rates / Spreads / FX / Oil: <b>FRED</b> &nbsp;·&nbsp; "
        "Equity indices: <b>Yahoo Finance</b>"
        "</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
