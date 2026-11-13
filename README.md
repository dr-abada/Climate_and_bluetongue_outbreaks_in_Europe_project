# Climate_and_bluetongue_outbreaks_in_Europe_(2005-2025)
# Temperature anomalies and bluetongue outbreaks in Europe

A small, reproducible analysis of whether warmer-than-usual years are associated with more
bluetongue outbreaks in European countries.

**Author:** Ali ABADA, DVM · MSc student · Predictive and Integrative Animal Biology · (Université Paris-Saclay / AgroParisTech / INRAE)

## Data

| Dataset | Source | Content |
| --- | --- | --- |
| Bluetongue outbreaks | [EU Animal Disease Information System (ADIS)](https://food.ec.europa.eu/animals/animal-diseases/animal-disease-information-system-adis_en) | Official outbreak notifications, extracted from the annual overviews and aggregated by country and year |
| Temperature anomalies | [Our World in Data](https://ourworldindata.org/grapher/annual-temperature-anomalies), derived from Copernicus ERA5 | Annual anomaly per country vs 1991–2020 |
| Country boundaries | [Natural Earth](https://www.naturalearthdata.com/) via `rnaturalearth` | Map polygons |

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
