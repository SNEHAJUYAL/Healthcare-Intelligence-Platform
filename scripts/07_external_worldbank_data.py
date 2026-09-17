"""
External Dataset Integration — World Bank Open Data
Healthcare Intelligence Platform

Unlike the Reality Check stage (which hardcodes individually-cited published
figures), this script pulls a genuine external DATASET live from a public
API and caches it to disk: the World Bank's health-system indicators for
the US and five peer countries.

Source: World Bank Open Data, World Development Indicators
        https://data.worldbank.org/  (API: https://api.worldbank.org/v2/)
        License: CC BY 4.0 (https://datacatalog.worldbank.org/public-licenses)
        No API key required; retrieved 2026-09.

Why this dataset: the platform's own admission-level data has no real
bed-capacity, staffing, or geographic field (Stage 7, Resource Planning,
flags this explicitly). Hospital beds/physicians per capita and health
spend are the closest real, freely-available substitute for that missing
context, at national scale.
"""
import json
import time
from pathlib import Path

import pandas as pd
import requests

BASE = Path(__file__).resolve().parents[1]
EXT_DIR = BASE / "data" / "external"
EXT_DIR.mkdir(exist_ok=True)

API = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"
COUNTRIES = {
    "USA": "United States", "GBR": "United Kingdom", "DEU": "Germany",
    "CAN": "Canada", "FRA": "France", "JPN": "Japan",
}
INDICATORS = {
    "SH.MED.BEDS.ZS": "Hospital beds (per 1,000 people)",
    "SH.MED.PHYS.ZS": "Physicians (per 1,000 people)",
    "SH.XPD.CHEX.PC.CD": "Health expenditure per capita (current US$)",
    "SH.XPD.CHEX.GD.ZS": "Health expenditure (% of GDP)",
    "SP.DYN.LE00.IN": "Life expectancy at birth (years)",
    "SH.UHC.OOPC.ZS": "Out-of-pocket health spending (% of current health expenditure)",
}

country_codes = ";".join(COUNTRIES.keys())
rows = []
for code, label in INDICATORS.items():
    url = API.format(countries=country_codes, indicator=code)
    resp = requests.get(url, params={"format": "json", "per_page": 2000, "date": "2000:2024"}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if len(payload) < 2 or payload[1] is None:
        print(f"WARNING: no data returned for {code}")
        continue
    for rec in payload[1]:
        if rec["value"] is None:
            continue
        rows.append({
            "indicator_code": code,
            "indicator": label,
            "country_code": rec["countryiso3code"],
            "country": rec["country"]["value"],
            "year": int(rec["date"]),
            "value": rec["value"],
        })
    time.sleep(0.2)  # be polite to the public API

df = pd.DataFrame(rows).sort_values(["indicator", "country", "year"])
raw_out = EXT_DIR / "worldbank_health_indicators.csv"
df.to_csv(raw_out, index=False)
print(f"Cached {len(df):,} real World Bank observations -> {raw_out}")

# ---- latest available value per country per indicator ----
latest = (df.sort_values("year").groupby(["indicator", "country"]).tail(1)
          .pivot(index="country", columns="indicator", values="value").round(2))
latest_year = (df.sort_values("year").groupby(["indicator", "country"]).tail(1)
               .pivot(index="country", columns="indicator", values="year"))

# ---- US trend across years, per indicator ----
us_trend = {
    label: df[(df["indicator"] == label) & (df["country_code"] == "USA")][["year", "value"]]
            .sort_values("year").to_dict("records")
    for label in INDICATORS.values()
}

snapshot = {}
for country in COUNTRIES.values():
    snapshot[country] = {}
    for label in INDICATORS.values():
        if country in latest.index and label in latest.columns and pd.notna(latest.loc[country, label]):
            snapshot[country][label] = {
                "value": latest.loc[country, label],
                "year": int(latest_year.loc[country, label]),
            }

output = {
    "source": "World Bank Open Data (World Development Indicators)",
    "url": "https://data.worldbank.org/indicator",
    "license": "CC BY 4.0",
    "retrieved": "2026-09",
    "note": (
        "This platform's own dataset has no real bed-capacity, staffing, or geographic field "
        "(see Stage 7, Resource Planning). These national-level indicators are the closest real, "
        "freely-available substitute for that missing context."
    ),
    "latest_snapshot_by_country": snapshot,
    "us_trend": us_trend,
}
OUT = BASE / "data" / "model" / "external_context.json"
OUT.write_text(json.dumps(output, indent=2, default=str))
print(f"Wrote external context summary -> {OUT}")
print("\nLatest snapshot:")
print(latest)
