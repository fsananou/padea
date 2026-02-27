#!/usr/bin/env python3
"""
Inflation & Commodity Price Dashboard — Annual Frequency
=========================================================
Annual historical + forecast data for inflation components and oil prices.
Sources: IMF WEO · IMF IFS · World Bank WDI · ECB SDW · FRED

Run locally :  python inflation_dashboard.py
               streamlit run inflation_dashboard.py
Online      :  deploy this file + requirements_dashboard.txt to Streamlit Cloud
"""

# ── Auto-launch when executed directly (python inflation_dashboard.py) ─────────
import sys, os
if __name__ == "__main__" and "streamlit" not in sys.modules:
    import subprocess
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)],
        check=False,
    )
    sys.exit(0)

# ── Imports ────────────────────────────────────────────────────────────────────
import io, time
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Inflation & Commodity Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """<style>
    .block-container{padding-top:1.5rem}
    .stMetric{background:#f8fafc;border-radius:8px;
              padding:.6rem 1rem;border:1px solid #e2e8f0}
    </style>""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# COUNTRY CATALOG
# iso2  → IMF IFS / World Bank / ECB
# weo   → IMF WEO (ISO alpha-3 or WEO area code)
# ecb   → ECB SDW country code (None = not covered)
# ─────────────────────────────────────────────────────────────────────────────
COUNTRIES: dict[str, dict] = {
    # ── Advanced Economies ─────────────────────────────────────────────────
    "United States":       {"iso2": "US",  "weo": "USA",  "ecb": None},
    "Euro Area":           {"iso2": "U2",  "weo": "EURO", "ecb": "U2"},
    "Germany":             {"iso2": "DE",  "weo": "DEU",  "ecb": "DE"},
    "France":              {"iso2": "FR",  "weo": "FRA",  "ecb": "FR"},
    "Italy":               {"iso2": "IT",  "weo": "ITA",  "ecb": "IT"},
    "Spain":               {"iso2": "ES",  "weo": "ESP",  "ecb": "ES"},
    "Netherlands":         {"iso2": "NL",  "weo": "NLD",  "ecb": "NL"},
    "Belgium":             {"iso2": "BE",  "weo": "BEL",  "ecb": "BE"},
    "Austria":             {"iso2": "AT",  "weo": "AUT",  "ecb": "AT"},
    "Portugal":            {"iso2": "PT",  "weo": "PRT",  "ecb": "PT"},
    "Greece":              {"iso2": "GR",  "weo": "GRC",  "ecb": "GR"},
    "Ireland":             {"iso2": "IE",  "weo": "IRL",  "ecb": "IE"},
    "Finland":             {"iso2": "FI",  "weo": "FIN",  "ecb": "FI"},
    "Luxembourg":          {"iso2": "LU",  "weo": "LUX",  "ecb": "LU"},
    "Slovakia":            {"iso2": "SK",  "weo": "SVK",  "ecb": "SK"},
    "Slovenia":            {"iso2": "SI",  "weo": "SVN",  "ecb": "SI"},
    "Estonia":             {"iso2": "EE",  "weo": "EST",  "ecb": "EE"},
    "Latvia":              {"iso2": "LV",  "weo": "LVA",  "ecb": "LV"},
    "Lithuania":           {"iso2": "LT",  "weo": "LTU",  "ecb": "LT"},
    "Croatia":             {"iso2": "HR",  "weo": "HRV",  "ecb": "HR"},
    "United Kingdom":      {"iso2": "GB",  "weo": "GBR",  "ecb": None},
    "Japan":               {"iso2": "JP",  "weo": "JPN",  "ecb": None},
    "Canada":              {"iso2": "CA",  "weo": "CAN",  "ecb": None},
    "Australia":           {"iso2": "AU",  "weo": "AUS",  "ecb": None},
    "New Zealand":         {"iso2": "NZ",  "weo": "NZL",  "ecb": None},
    "Switzerland":         {"iso2": "CH",  "weo": "CHE",  "ecb": None},
    "Sweden":              {"iso2": "SE",  "weo": "SWE",  "ecb": "SE"},
    "Norway":              {"iso2": "NO",  "weo": "NOR",  "ecb": None},
    "Denmark":             {"iso2": "DK",  "weo": "DNK",  "ecb": "DK"},
    "Iceland":             {"iso2": "IS",  "weo": "ISL",  "ecb": None},
    # ── Eastern Europe ────────────────────────────────────────────────────
    "Poland":              {"iso2": "PL",  "weo": "POL",  "ecb": None},
    "Czech Republic":      {"iso2": "CZ",  "weo": "CZE",  "ecb": None},
    "Hungary":             {"iso2": "HU",  "weo": "HUN",  "ecb": None},
    "Romania":             {"iso2": "RO",  "weo": "ROU",  "ecb": None},
    "Bulgaria":            {"iso2": "BG",  "weo": "BGR",  "ecb": None},
    # ── Asia-Pacific ──────────────────────────────────────────────────────
    "China":               {"iso2": "CN",  "weo": "CHN",  "ecb": None},
    "India":               {"iso2": "IN",  "weo": "IND",  "ecb": None},
    "South Korea":         {"iso2": "KR",  "weo": "KOR",  "ecb": None},
    "Indonesia":           {"iso2": "ID",  "weo": "IDN",  "ecb": None},
    "Malaysia":            {"iso2": "MY",  "weo": "MYS",  "ecb": None},
    "Thailand":            {"iso2": "TH",  "weo": "THA",  "ecb": None},
    "Philippines":         {"iso2": "PH",  "weo": "PHL",  "ecb": None},
    "Vietnam":             {"iso2": "VN",  "weo": "VNM",  "ecb": None},
    "Singapore":           {"iso2": "SG",  "weo": "SGP",  "ecb": None},
    "Pakistan":            {"iso2": "PK",  "weo": "PAK",  "ecb": None},
    "Bangladesh":          {"iso2": "BD",  "weo": "BGD",  "ecb": None},
    # ── Latin America ─────────────────────────────────────────────────────
    "Brazil":              {"iso2": "BR",  "weo": "BRA",  "ecb": None},
    "Mexico":              {"iso2": "MX",  "weo": "MEX",  "ecb": None},
    "Argentina":           {"iso2": "AR",  "weo": "ARG",  "ecb": None},
    "Chile":               {"iso2": "CL",  "weo": "CHL",  "ecb": None},
    "Colombia":            {"iso2": "CO",  "weo": "COL",  "ecb": None},
    "Peru":                {"iso2": "PE",  "weo": "PER",  "ecb": None},
    "Bolivia":             {"iso2": "BO",  "weo": "BOL",  "ecb": None},
    "Ecuador":             {"iso2": "EC",  "weo": "ECU",  "ecb": None},
    "Uruguay":             {"iso2": "UY",  "weo": "URY",  "ecb": None},
    "Paraguay":            {"iso2": "PY",  "weo": "PRY",  "ecb": None},
    "Venezuela":           {"iso2": "VE",  "weo": "VEN",  "ecb": None},
    # ── Middle East & North Africa ────────────────────────────────────────
    "Saudi Arabia":        {"iso2": "SA",  "weo": "SAU",  "ecb": None},
    "UAE":                 {"iso2": "AE",  "weo": "ARE",  "ecb": None},
    "Turkey":              {"iso2": "TR",  "weo": "TUR",  "ecb": None},
    "Israel":              {"iso2": "IL",  "weo": "ISR",  "ecb": None},
    "Egypt":               {"iso2": "EG",  "weo": "EGY",  "ecb": None},
    "Morocco":             {"iso2": "MA",  "weo": "MAR",  "ecb": None},
    "Tunisia":             {"iso2": "TN",  "weo": "TUN",  "ecb": None},
    "Algeria":             {"iso2": "DZ",  "weo": "DZA",  "ecb": None},
    "Libya":               {"iso2": "LY",  "weo": "LBY",  "ecb": None},
    "Iran":                {"iso2": "IR",  "weo": "IRN",  "ecb": None},
    "Iraq":                {"iso2": "IQ",  "weo": "IRQ",  "ecb": None},
    "Jordan":              {"iso2": "JO",  "weo": "JOR",  "ecb": None},
    "Lebanon":             {"iso2": "LB",  "weo": "LBN",  "ecb": None},
    # ── Sub-Saharan Africa ────────────────────────────────────────────────
    "South Africa":        {"iso2": "ZA",  "weo": "ZAF",  "ecb": None},
    "Nigeria":             {"iso2": "NG",  "weo": "NGA",  "ecb": None},
    "Kenya":               {"iso2": "KE",  "weo": "KEN",  "ecb": None},
    "Ethiopia":            {"iso2": "ET",  "weo": "ETH",  "ecb": None},
    "Ghana":               {"iso2": "GH",  "weo": "GHA",  "ecb": None},
    "Tanzania":            {"iso2": "TZ",  "weo": "TZA",  "ecb": None},
    "Uganda":              {"iso2": "UG",  "weo": "UGA",  "ecb": None},
    "Mozambique":          {"iso2": "MZ",  "weo": "MOZ",  "ecb": None},
    "Côte d'Ivoire":       {"iso2": "CI",  "weo": "CIV",  "ecb": None},
    "Senegal":             {"iso2": "SN",  "weo": "SEN",  "ecb": None},
    "Cameroon":            {"iso2": "CM",  "weo": "CMR",  "ecb": None},
    "Angola":              {"iso2": "AO",  "weo": "AGO",  "ecb": None},
    "Zambia":              {"iso2": "ZM",  "weo": "ZMB",  "ecb": None},
    "Zimbabwe":            {"iso2": "ZW",  "weo": "ZWE",  "ecb": None},
    # ── CIS / Eastern Europe ─────────────────────────────────────────────
    "Russia":              {"iso2": "RU",  "weo": "RUS",  "ecb": None},
    "Ukraine":             {"iso2": "UA",  "weo": "UKR",  "ecb": None},
    "Kazakhstan":          {"iso2": "KZ",  "weo": "KAZ",  "ecb": None},
    "Uzbekistan":          {"iso2": "UZ",  "weo": "UZB",  "ecb": None},
}

# ─────────────────────────────────────────────────────────────────────────────
# INDICATOR CATALOG
# ─────────────────────────────────────────────────────────────────────────────
# source      : "weo" | "ifs" | "wb" | "ecb" | "brent" | "wti"
# weo_code    : IMF WEO indicator code
# ifs_code    : IMF IFS annual series code (index → compute YoY)
# wb_code     : World Bank WDI indicator code
# ecb_comp    : ECB HICP component code
# ecb_meas    : "ANR" (% change) | "INX" (index)
# compute     : "direct" (value already in %) | "yoy" (pct_change(1)*100)
# ─────────────────────────────────────────────────────────────────────────────
INDICATORS: dict[str, dict] = {
    "CPI Inflation (YoY %)": {
        "sources": ["weo", "wb", "ifs", "ecb"],
        "weo_code":  "PCPIPCH",
        "ifs_code":  "PCPI_IX",
        "wb_code":   "FP.CPI.TOTL.ZG",
        "ecb_comp":  "000000", "ecb_meas": "ANR",
        "compute": "direct",   # WEO/WB already in %
        "unit": "%",
    },
    "Core CPI (YoY %, ex food & energy)": {
        "sources": ["ifs", "ecb"],
        "ifs_code":  "PCPIX_IX",
        "ecb_comp":  "XEF000", "ecb_meas": "ANR",
        "compute": "yoy",
        "unit": "%",
    },
    "Food CPI (YoY %)": {
        "sources": ["ifs", "ecb"],
        "ifs_code":  "PCPIF_IX",
        "ecb_comp":  "FOOD00", "ecb_meas": "ANR",
        "compute": "yoy",
        "unit": "%",
    },
    "Energy CPI (YoY %)": {
        "sources": ["ifs", "ecb"],
        "ifs_code":  "PCPIE_IX",
        "ecb_comp":  "NRG000", "ecb_meas": "ANR",
        "compute": "yoy",
        "unit": "%",
    },
    "Services CPI (YoY %)": {
        "sources": ["ecb"],
        "ecb_comp":  "SERV00", "ecb_meas": "ANR",
        "compute": "direct",
        "unit": "%",
    },
    "Goods CPI (YoY %)": {
        "sources": ["ecb"],
        "ecb_comp":  "IGDS00", "ecb_meas": "ANR",
        "compute": "direct",
        "unit": "%",
    },
    "PPI (YoY %)": {
        "sources": ["ifs"],
        "ifs_code":  "PPPI_IX",
        "compute": "yoy",
        "unit": "%",
    },
    "CPI Index (2010=100)": {
        "sources": ["wb", "ifs", "ecb"],
        "ifs_code":  "PCPI_IX",
        "wb_code":   "FP.CPI.TOTL",
        "ecb_comp":  "000000", "ecb_meas": "INX",
        "compute": "direct",
        "unit": "Index",
    },
    "Brent Crude Oil (USD/bbl)": {
        "sources": ["brent"],
        "unit": "USD/bbl",
    },
    "WTI Crude Oil (USD/bbl)": {
        "sources": ["wti"],
        "unit": "USD/bbl",
    },
    "Inflation Forecast (IMF WEO, YoY %)": {
        "sources": ["weo"],
        "weo_code":  "PCPIPCH",
        "compute": "direct",
        "unit": "%",
        "forecast_only": True,   # show both hist + forecast
    },
}

# API base URLs
IMF_IFS = "https://dataservices.imf.org/REST/SDMX_JSON.svc/CompactData/IFS"
ECB_URL = "https://data-api.ecb.europa.eu/service/data/ICP"
WEO_URL = "https://www.imf.org/external/datamapper/api/v1"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
WB_URL   = "https://api.worldbank.org/v2/country"

PALETTE = [
    "#1f77b4","#ff7f0e","#2ca02c","#d62728","#9467bd",
    "#8c564b","#e377c2","#7f7f7f","#bcbd22","#17becf",
    "#aec7e8","#ffbb78","#98df8a","#ff9896","#c5b0d5",
]

# ─────────────────────────────────────────────────────────────────────────────
# DATA FETCHING — all functions cached per session
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_imf_ifs_annual(iso2: str, code: str, start: int, end: int) -> pd.Series:
    """IMF IFS annual series (index). Returns pd.Series with YearEnd PeriodIndex."""
    url = f"{IMF_IFS}/A.{iso2}.{code}"
    try:
        r = requests.get(url,
                         params={"startPeriod": str(start), "endPeriod": str(end)},
                         timeout=30, headers={"Accept": "application/json"})
        r.raise_for_status()
        raw = r.json()
        series = raw.get("CompactData", {}).get("DataSet", {}).get("Series", {})
        if not series:
            return pd.Series(dtype=float)
        obs = series.get("Obs", [])
        if isinstance(obs, dict):
            obs = [obs]
        records: dict[pd.Period, float] = {}
        for o in obs:
            t = o.get("@TIME_PERIOD")
            v = o.get("@OBS_VALUE")
            if t and v:
                try:
                    records[pd.Period(t, freq="Y")] = float(v)
                except Exception:
                    pass
        s = pd.Series(records, dtype=float)
        if not s.empty:
            s.index = pd.PeriodIndex(s.index, freq="Y")
        return s.sort_index()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_ecb_annual(ecb_code: str, component: str, measure: str,
                     start: int, end: int) -> pd.Series:
    """ECB SDW annual HICP series."""
    key = f"A.{ecb_code}.N.{component}.4.{measure}"
    try:
        r = requests.get(f"{ECB_URL}/{key}",
                         params={"startPeriod": str(start), "endPeriod": str(end),
                                 "format": "jsondata"},
                         timeout=30, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = r.json()
        datasets  = data.get("dataSets", [])
        structure = data.get("structure", {})
        if not datasets or not structure:
            return pd.Series(dtype=float)
        obs_dims = structure.get("dimensions", {}).get("observation", [])
        time_vals: list[str] = []
        for dim in obs_dims:
            if dim.get("id") == "TIME_PERIOD":
                time_vals = [v["id"] for v in dim.get("values", [])]
                break
        if not time_vals:
            return pd.Series(dtype=float)
        series_dict = datasets[0].get("series", {})
        if not series_dict:
            return pd.Series(dtype=float)
        obs = list(series_dict.values())[0].get("observations", {})
        records: dict[pd.Period, float] = {}
        for idx_str, val_list in obs.items():
            idx = int(idx_str)
            if idx < len(time_vals) and val_list and val_list[0] is not None:
                try:
                    records[pd.Period(time_vals[idx], freq="Y")] = float(val_list[0])
                except Exception:
                    pass
        s = pd.Series(records, dtype=float)
        if not s.empty:
            s.index = pd.PeriodIndex(s.index, freq="Y")
        return s.sort_index()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=86_400, show_spinner=False)
def fetch_imf_weo(weo_code: str, weo_iso: str) -> tuple[pd.Series, int]:
    """IMF WEO: annual data + forecasts. Returns (series, last_actual_year)."""
    try:
        r = requests.get(f"{WEO_URL}/{weo_code}/{weo_iso}", timeout=30)
        r.raise_for_status()
        data  = r.json()
        vals  = data.get("values", {}).get(weo_code, {}).get(weo_iso, {})
        last_actual = int(
            data.get("info", {}).get(weo_code, {}).get("lastActual",
                                                         str(datetime.now().year - 1))
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


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_world_bank(iso2: str, wb_code: str, start: int, end: int) -> pd.Series:
    """World Bank WDI: annual series."""
    url = f"{WB_URL}/{iso2}/indicator/{wb_code}"
    try:
        r = requests.get(url,
                         params={"format": "json", "mrv": end - start + 5,
                                 "date": f"{start}:{end}", "per_page": 100},
                         timeout=30)
        r.raise_for_status()
        payload = r.json()
        if len(payload) < 2 or not payload[1]:
            return pd.Series(dtype=float)
        records: dict[pd.Period, float] = {}
        for obs in payload[1]:
            yr  = obs.get("date")
            val = obs.get("value")
            if yr and val is not None:
                try:
                    records[pd.Period(yr, freq="Y")] = float(val)
                except Exception:
                    pass
        s = pd.Series(records, dtype=float)
        if not s.empty:
            s.index = pd.PeriodIndex(s.index, freq="Y")
        return s.sort_index()
    except Exception:
        return pd.Series(dtype=float)


@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_fred_annual(series_id: str) -> pd.Series:
    """FRED: daily oil prices → annual average."""
    try:
        r = requests.get(FRED_URL, params={"id": series_id}, timeout=30)
        r.raise_for_status()
        df = pd.read_csv(io.StringIO(r.text), parse_dates=["DATE"])
        df.columns = ["date", "value"]
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

def yoy_from_index(s: pd.Series) -> pd.Series:
    """Annual YoY % from an index series."""
    return s.pct_change(1) * 100.0


def clip_years(s: pd.Series, start: int, end: int) -> pd.Series:
    if s.empty:
        return s
    try:
        ps, pe = pd.Period(start, freq="Y"), pd.Period(end, freq="Y")
        return s[(s.index >= ps) & (s.index <= pe)]
    except Exception:
        return s


def to_datetime(s: pd.Series) -> pd.Series:
    """PeriodIndex → DatetimeIndex for Plotly."""
    s2 = s.copy()
    s2.index = s.index.to_timestamp()
    return s2


# ─────────────────────────────────────────────────────────────────────────────
# DATA ASSEMBLY
# Returns (historical, forecast, unit, source_label)
# ─────────────────────────────────────────────────────────────────────────────

def get_series(
    country: str,
    indicator: str,
    start_yr: int,
    end_yr: int,
    prefer_ecb: bool = True,
    include_forecast: bool = True,
) -> tuple[pd.Series, pd.Series, str, str]:
    """
    Robust version:
    - Tries ALL possible sources for the indicator
    - Keeps the first non-empty historical series
    - Keeps the first non-empty forecast series (WEO only)
    - Guarantees fallback across WEO → ECB → WB → IFS
    """
    cfg  = INDICATORS[indicator]
    ccfg = COUNTRIES[country]
    unit = cfg.get("unit", "")
    sources = cfg.get("sources", [])

    empty = pd.Series(dtype=float)
    hist_candidates = []
    fcast_candidates = []
    source_labels = []

    # --- Oil prices (country-independent) ---
    if "brent" in sources:
        s = clip_years(fetch_fred_annual("DCOILBRENTEU"), start_yr, end_yr)
        return s, empty, unit, "FRED"

    if "wti" in sources:
        s = clip_years(fetch_fred_annual("DCOILWTICO"), start_yr, end_yr)
        return s, empty, unit, "FRED"

    # --- IMF WEO (includes forecasts) ---
    if "weo" in sources:
        weo_iso = ccfg.get("weo")
        if weo_iso:
            ann, last_actual = fetch_imf_weo(cfg["weo_code"], weo_iso)
            if not ann.empty:
                cut = pd.Period(last_actual, freq="Y")
                hist = clip_years(ann[ann.index <= cut], start_yr, end_yr)
                fcast = clip_years(ann[ann.index > cut], start_yr, end_yr) if include_forecast else empty
                if not hist.empty:
                    hist_candidates.append(hist)
                    fcast_candidates.append(fcast)
                    source_labels.append("IMF WEO")

    # --- ECB HICP (preferred for Euro area) ---
    if "ecb" in sources and prefer_ecb:
        ecb_code = ccfg.get("ecb")
        comp = cfg.get("ecb_comp")
        meas = cfg.get("ecb_meas", "ANR")
        compute = cfg.get("compute", "yoy")

        if ecb_code and comp:
            raw = fetch_ecb_annual(ecb_code, comp, meas, start_yr - 1, end_yr)
            if not raw.empty:
                if compute == "yoy" and meas != "ANR":
                    raw = yoy_from_index(raw)
                hist = clip_years(raw, start_yr, end_yr)
                if not hist.empty:
                    hist_candidates.append(hist)
                    fcast_candidates.append(empty)
                    source_labels.append("ECB")

    # --- World Bank WDI ---
    if "wb" in sources:
        wb_code = cfg.get("wb_code")
        if wb_code:
            wb = fetch_world_bank(ccfg["iso2"], wb_code, start_yr, end_yr)
            if not wb.empty:
                hist_candidates.append(wb)
                fcast_candidates.append(empty)
                source_labels.append("World Bank")

    # --- IMF IFS ---
    if "ifs" in sources:
        ifs_code = cfg.get("ifs_code")
        iso2 = ccfg.get("iso2")
        compute = cfg.get("compute", "yoy")

        if ifs_code and iso2:
            ext = start_yr - 2 if compute == "yoy" else start_yr
            raw = fetch_imf_ifs_annual(iso2, ifs_code, ext, end_yr)
            if not raw.empty:
                s = yoy_from_index(raw) if compute == "yoy" else raw
                hist = clip_years(s, start_yr, end_yr)
                if not hist.empty:
                    hist_candidates.append(hist)
                    fcast_candidates.append(empty)
                    source_labels.append("IMF IFS")

    # --- Final selection ---
    if hist_candidates:
        return hist_candidates[0], fcast_candidates[0], unit, source_labels[0]

    return empty, empty, unit, "—"


# ─────────────────────────────────────────────────────────────────────────────
# CHART BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def build_chart(
    traces: list[dict],  # [{label, hist, fcast, unit, color}]
    title: str,
) -> go.Figure:
    units = list(dict.fromkeys(t["unit"] for t in traces if not t["hist"].empty or not t["fcast"].empty))
    dual  = len(units) >= 2

    fig = make_subplots(specs=[[{"secondary_y": True}]]) if dual else go.Figure()
    unit1 = units[0] if units else ""
    unit2 = units[1] if len(units) > 1 else unit1

    def _add(s: pd.Series, name: str, color: str, dash: str, unit: str,
             show_legend: bool = True):
        if s.empty:
            return
        is_sec = dual and unit != unit1
        tr = go.Scatter(
            x=to_datetime(s).index,
            y=s.values,
            name=name,
            line=dict(color=color, width=2, dash=dash),
            mode="lines",
            legendgroup=name.split(" (")[0],
            showlegend=show_legend,
            hovertemplate=f"<b>{name}</b><br>%{{x|%Y}}: %{{y:.2f}} {unit}<extra></extra>",
        )
        if dual:
            fig.add_trace(tr, secondary_y=is_sec)
        else:
            fig.add_trace(tr)

    for t in traces:
        _add(t["hist"],  t["label"],               t["color"], "solid", t["unit"])
        _add(t["fcast"], t["label"] + " (forecast)", t["color"], "dash",  t["unit"],
             show_legend=not t["hist"].empty)

    fig.update_layout(
        title=dict(text=title, font=dict(size=15, color="#1f2937")),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1, bgcolor="rgba(255,255,255,0.85)",
                    font=dict(size=11)),
        plot_bgcolor="white", paper_bgcolor="white",
        xaxis=dict(showgrid=True, gridcolor="#f0f0f0",
                   showline=True, linecolor="#d1d5db"),
        yaxis=dict(showgrid=True, gridcolor="#f0f0f0",
                   showline=True, linecolor="#d1d5db"),
        margin=dict(l=60, r=60, t=70, b=50),
        height=460,
    )
    if dual:
        fig.update_yaxes(title_text=unit1, secondary_y=False)
        fig.update_yaxes(title_text=unit2, secondary_y=True, showgrid=False)
    elif units:
        fig.update_yaxes(title_text=unit1)
    if any("%" in t.get("unit", "") for t in traces):
        fig.add_hline(y=0, line_dash="dot", line_color="#94a3b8", line_width=1)

    return fig


# ─────────────────────────────────────────────────────────────────────────────
# STREAMLIT APP
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    st.title("📈 Inflation & Commodity Price Dashboard")
    st.caption(
        "Annual data · Sources: IMF WEO · IMF IFS · World Bank · ECB · FRED  "
        "| Dashed lines = forecast"
    )
    st.divider()

    this_year = datetime.now().year

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("⚙️ Settings")

        compare_mode = st.toggle(
            "Multi-country comparison",
            help="Compare one indicator across several countries",
        )

        st.subheader("Countries")
        country_list = sorted(COUNTRIES.keys())

        if compare_mode:
            sel_countries = st.multiselect(
                "Countries (up to 10)",
                options=country_list,
                default=["United States", "Euro Area", "United Kingdom", "China"],
                max_selections=10,
            )
        else:
            sel_country = st.selectbox(
                "Country", country_list,
                index=country_list.index("United States"),
            )
            sel_countries = [sel_country]

        st.subheader("Indicators")
        ind_list = list(INDICATORS.keys())

        if compare_mode:
            sel_indicators = [st.selectbox("Indicator", ind_list, index=0)]
        else:
            sel_indicators = st.multiselect(
                "Indicators",
                ind_list,
                default=["CPI Inflation (YoY %)", "Core CPI (YoY %, ex food & energy)"],
            )

        st.subheader("Period")
        year_opts = list(range(1980, this_year + 7))
        start_yr  = st.selectbox("Start year", year_opts,
                                  index=year_opts.index(2000))
        end_yr    = st.selectbox("End year", year_opts,
                                  index=year_opts.index(min(this_year + 5, year_opts[-1])))

        st.subheader("Options")
        prefer_ecb       = st.toggle("Prefer ECB for Euro area countries", value=True)
        include_forecast = st.toggle("Include IMF WEO forecasts", value=True)

        fetch_btn = st.button("🔄 Fetch Data", type="primary", use_container_width=True)

    # ── Validate ──────────────────────────────────────────────────────────────
    if not sel_countries:
        st.info("Select at least one country.")
        return
    if not sel_indicators:
        st.info("Select at least one indicator.")
        return
    if start_yr >= end_yr:
        st.error("Start year must be before end year.")
        return

    # ── Fetch / cache ─────────────────────────────────────────────────────────
    fetch_key = (
        tuple(sorted(sel_countries)), tuple(sorted(sel_indicators)),
        start_yr, end_yr, prefer_ecb, include_forecast,
    )
    if "data_cache" not in st.session_state:
        st.session_state.data_cache = {}
        st.session_state.fetch_key  = None

    if fetch_btn or st.session_state.fetch_key != fetch_key:
        st.session_state.fetch_key = fetch_key
        total = len(sel_countries) * len(sel_indicators)
        prog  = st.progress(0, text="Fetching data…")
        cache: dict[str, tuple] = {}
        n = 0
        for country in sel_countries:
            for ind in sel_indicators:
                prog.progress(n / total, text=f"{country} · {ind}")
                hist, fcast, unit, src = get_series(
                    country, ind, start_yr, end_yr, prefer_ecb, include_forecast
                )
                cache[f"{country}::{ind}"] = (hist, fcast, unit, src)
                n += 1
                time.sleep(0.05)
        prog.empty()
        st.session_state.data_cache = cache

    data = st.session_state.data_cache
    if not data:
        st.warning("No data yet — click **Fetch Data**.")
        return

    if all(h.empty and f.empty for h, f, _, _ in data.values()):
        st.warning(
            "No data returned. Try different countries/indicators or a shorter range. "
            "Some indicators (Core CPI, Services…) are only available for Euro area countries."
        )
        return

    # ── KPI cards (single-country mode) ──────────────────────────────────────
    if not compare_mode and sel_countries:
        country = sel_countries[0]
        kpis = []
        for ind in sel_indicators[:4]:
            h, f, unit, src = data.get(f"{country}::{ind}",
                                        (pd.Series(dtype=float), pd.Series(dtype=float), "", ""))
            full = pd.concat([h, f]).dropna().sort_index()
            if not full.empty:
                last_val = full.iloc[-1]
                last_yr  = full.index[-1]
                delta    = None
                if len(full) >= 2:
                    prev = full.iloc[-2]
                    delta = f"{last_val - prev:+.2f} {unit} vs prev. year"
                kpis.append((ind, last_val, unit, last_yr, delta, src))

        if kpis:
            cols = st.columns(len(kpis))
            for col, (ind, val, unit, period, delta, src) in zip(cols, kpis):
                col.metric(
                    label=ind[:38] + ("…" if len(ind) > 38 else ""),
                    value=f"{val:.2f} {unit}",
                    delta=delta,
                    help=f"Last data: {period}  |  Source: {src}",
                )
            st.divider()

    # ── Charts ────────────────────────────────────────────────────────────────
    if compare_mode:
        for ind in sel_indicators:
            traces = []
            for i, country in enumerate(sel_countries):
                h, f, unit, _ = data.get(f"{country}::{ind}",
                                          (pd.Series(dtype=float), pd.Series(dtype=float), "", ""))
                if not h.empty or not f.empty:
                    traces.append({"label": country, "hist": h, "fcast": f,
                                   "unit": unit, "color": PALETTE[i % len(PALETTE)]})
            if traces:
                st.plotly_chart(
                    build_chart(traces, f"{ind} — Country Comparison"),
                    use_container_width=True,
                )
    else:
        for country in sel_countries:
            traces = []
            for i, ind in enumerate(sel_indicators):
                h, f, unit, _ = data.get(f"{country}::{ind}",
                                          (pd.Series(dtype=float), pd.Series(dtype=float), "", ""))
                if not h.empty or not f.empty:
                    traces.append({"label": ind, "hist": h, "fcast": f,
                                   "unit": unit, "color": PALETTE[i % len(PALETTE)]})
            if traces:
                st.plotly_chart(
                    build_chart(traces, f"{country} — Macro Indicators"),
                    use_container_width=True,
                )

    # ── Data table & download ─────────────────────────────────────────────────
    with st.expander("📋 Data table & Download"):
        frames = []
        for key, (h, f, unit, src) in data.items():
            c_name, i_name = key.split("::", 1)
            col = (f"{c_name} | {i_name} ({unit})" if compare_mode
                   else f"{i_name} ({unit})")
            full = pd.concat([h, f]).sort_index()
            if not full.empty:
                df_tmp = full.rename(col).to_frame()
                df_tmp.index = [str(p) for p in df_tmp.index]
                frames.append(df_tmp)

        if frames:
            combined = pd.concat(frames, axis=1).sort_index(ascending=False).round(3)
            st.dataframe(combined, use_container_width=True, height=380)
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇️ CSV", combined.to_csv(),
                                   "inflation_data.csv", "text/csv",
                                   use_container_width=True)
            with c2:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    combined.to_excel(w, sheet_name="Data")
                st.download_button("⬇️ Excel", buf.getvalue(), "inflation_data.xlsx",
                                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   use_container_width=True)

    # ── Source legend ─────────────────────────────────────────────────────────
    if not compare_mode and sel_countries:
        sources_used = {data[k][3] for k in data if not data[k][0].empty or not data[k][1].empty}
        if sources_used - {"—"}:
            with st.expander("ℹ️ Data sources used"):
                st.markdown(
                    "| Indicator | Source |\n|---|---|\n" +
                    "\n".join(
                        f"| {k.split('::')[1]} | {v[3]} |"
                        for k, v in data.items() if not v[0].empty or not v[1].empty
                    )
                )

    st.divider()
    st.markdown(
        "**Sources** · **IMF WEO**: headline inflation + 5-year forecasts (all countries) "
        "· **IMF IFS**: CPI/PPI components (annual index series) "
        "· **World Bank WDI**: CPI level & growth fallback "
        "· **ECB SDW**: HICP for Euro area members "
        "· **FRED**: Brent & WTI crude oil daily → annual average  \n"
        "*Dashed lines = IMF WEO forecast. Forecasts extend to ~5 years ahead.*"
    )


if __name__ == "__main__":
    main()
