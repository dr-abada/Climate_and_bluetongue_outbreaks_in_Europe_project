# Temperature anomalies and bluetongue outbreaks in Europe

A small, reproducible analysis of whether warmer-than-usual years are associated with more
bluetongue outbreaks in European countries.

**Author:** Ali ABADA, DVM · MSc student, M2 PRIAM (Université Paris-Saclay / AgroParisTech / INRAE)

## Data

| Dataset | Source | Content |
| --- | --- | --- |
| Bluetongue outbreaks | [EU Animal Disease Information System (ADIS)](https://food.ec.europa.eu/animals/animal-diseases/animal-disease-information-system-adis_en) | Official outbreak notifications, extracted from the annual overviews and aggregated by country and year |
| Temperature anomalies | [Our World in Data](https://ourworldindata.org/grapher/annual-temperature-anomalies), derived from Copernicus ERA5 | Annual anomaly per country vs 1991–2020 |
| Country boundaries | [Natural Earth](https://www.naturalearthdata.com/) via `rnaturalearth` | Map polygons |

## Data extraction from ADIS reports

ADIS publishes its yearly outbreak overviews as PDF tables (one row per disease and serotype,
one column per country). `scripts/extract_adis_bluetongue.py` reads the 21 reports (2005–2025)
with `pdfplumber`, matches each count to its country column and disease row by position, and
writes:

- `data/raw/bluetongue_adis.csv`: outbreaks per country and year (199 country-years, 31 countries)
- `data/raw/bluetongue_adis_by_serotype.csv`: the same, split by serotype, with the source page

Validation: every integer in the summary tables is either assigned to a row and column or
listed for review (the 27 unassigned values are page numbers and footnotes); 2019 and 2024
were checked cell by cell against the PDFs; country codes were harmonised (ISO3 up to 2021,
ISO2 from 2022).

**Reporting change:** counts from 2021 onwards are much lower than before, coinciding with the
EU Animal Health Law (applied from 21 April 2021). The models include a reporting-period term.

## Methods

- Country-year panel with zero-filled years without outbreaks
- Poisson GLM (baseline) → negative-binomial GLM → negative-binomial GLMM with a country random intercept (`glmmTMB`)
- Residual checks with `DHARMa`; results as incidence rate ratios
- Choropleth map with `sf`

## How to reproduce

```r
source("R/00_setup.R")         # install/load packages
source("R/01_prepare_data.R")  # build data/processed/bt_climate_panel.csv
source("R/02_models.R")        # fit models, save output/models.rds
quarto::quarto_render("report.qmd")
```

## Repository structure

```
data/raw/          input files (ADIS extraction, OWID temperature CSV)
data/processed/    analysis panel
R/                 scripts, run in order
output/            models and figures
report.qmd         Quarto report
```

## Limitations

Notified outbreaks reflect reporting as well as disease; vaccination and serotype incursions are
not modelled; climate data are national and annual. See the report for details.
