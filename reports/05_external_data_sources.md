# External Dataset Integration — World Bank Open Data
### Healthcare Intelligence Platform

Everything through the Reality Check report (`04_reality_check.md`) compares
the platform against individually-cited published *statistics*. This stage
goes one step further: it pulls a genuine external **dataset** live from a
public API and caches it in the repository as a real, versioned file —
`data/external/worldbank_health_indicators.csv`.

## Why this dataset

The platform's own admission-level data has no bed-capacity, staffing, or
geographic field — Stage 7 (Resource Planning) flags this gap explicitly
and calls its own figures "capacity-demand proxies," not real utilization.
Hospital beds and physicians per capita, and national health spend, are the
closest real, freely-available substitute for that missing context at
national scale.

## Source

- **Provider:** World Bank Open Data, World Development Indicators
- **API:** `https://api.worldbank.org/v2/` (no key required)
- **License:** [CC BY 4.0](https://datacatalog.worldbank.org/public-licenses)
- **Retrieved:** 2026-09, by [`scripts/07_external_worldbank_data.py`](../scripts/07_external_worldbank_data.py)
- **Coverage:** United States + 5 peer countries (UK, Germany, Canada, France, Japan), 2000–2024, 692 real observations across 5 indicators

## Latest snapshot (most recent year available per country)

| Country | Hospital beds /1,000 | Physicians /1,000 | Health spend / capita | Health spend (% GDP) | Life expectancy |
|---|---|---|---|---|---|
| United States | 2.68 (2022) | 3.68 (2022) | $13,473 (2023) | 16.69% (2023) | 78.9 yrs (2024) |
| United Kingdom | 2.42 (2022) | 3.30 (2023) | $5,860 (2024) | 11.13% (2024) | 81.4 yrs (2024) |
| Germany | 7.55 (2023) | 4.53 (2022) | $6,849 (2024) | 12.27% (2024) | 80.8 yrs (2024) |
| Canada | 2.54 (2022) | 2.82 (2023) | $6,378 (2024) | 11.31% (2024) | 82.1 yrs (2024) |
| France | 5.65 (2022) | 3.28 (2022) | $5,327 (2024) | 11.54% (2024) | 83.0 yrs (2024) |
| Japan | 12.59 (2022) | 2.65 (2022) | $3,638 (2023) | 10.74% (2023) | 84.0 yrs (2024) |

Each cell is independently the latest year the World Bank had published for
that country/indicator at fetch time (years differ by column because
countries report on different cycles) — see `data/model/external_context.json`
for the full multi-year series behind every cell.

## What this adds to the platform

1. **A real capacity benchmark for Resource Planning.** The platform cannot
   say anything about real bed utilization — but it can now say the US
   national average is 2.68 beds per 1,000 people, less than a **quarter of
   Japan's** (12.59) and well below Germany's (7.55) — context for why any
   US capacity-planning conversation runs tighter than international peers.
2. **A cost-structure anchor for Financial Analytics.** US health spend is
   16.69% of GDP and $13,473 per capita — both the highest of any country
   in this comparison by a wide margin (Germany, the next-highest, spends
   12.27% of GDP and $6,849 per capita). The platform's own $25,594 average
   billing per admission should be read against this backdrop: a single US
   hospital admission in this dataset costs roughly **1.9x the entire
   annual per-capita health spend** of the country.
3. **Physicians-per-capita context for Doctor Performance.** The US (3.68
   per 1,000) sits second in this comparison, behind Germany (4.53, the
   highest) and above the UK, Canada, France, and Japan (2.65–3.30). Japan
   is the striking outlier: lowest physician density here (2.65) paired
   with by far the most hospital beds (12.59) — bed supply and physician
   supply are independent capacity levers, not the same constraint.

## Honesty notes

- This is national-level, aggregate data — it cannot be joined row-by-row
  to the platform's synthetic admissions (which have no country/state
  field). It's context, not a merged dimension table.
- `SH.UHC.OOPC.ZS` (out-of-pocket spending share) returned no data from the
  API for this country set at fetch time and was dropped rather than
  backfilled with an estimate.
- Re-running `scripts/07_external_worldbank_data.py` re-fetches live from
  the API — figures will drift slightly as the World Bank revises recent
  years, which is expected and correct behavior for an external live
  source rather than a static snapshot.
