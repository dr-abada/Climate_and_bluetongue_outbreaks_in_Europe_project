# 01_prepare_data.R -- build the analysis dataset
# Inputs (data/raw/):
#   bluetongue_adis.csv            columns: country, year, outbreaks, source
#   annual-temperature-anomalies.csv  downloaded from Our World in Data (ERA5-based)
# Output (data/processed/):
#   bt_climate_panel.csv           one row per country x year, zeros filled in

library(tidyverse)
library(countrycode)
library(here)

# ---- 1. Bluetongue outbreaks (EU ADIS) -------------------------------------
bt_raw <- read_csv(here("data", "raw", "bluetongue_adis.csv"), show_col_types = FALSE)

# The ADIS extraction already provides ISO3 codes; fall back to country names otherwise.
if (!"iso3" %in% names(bt_raw)) {
  bt_raw <- bt_raw |>
    mutate(iso3 = countrycode(country, origin = "country.name", destination = "iso3c"))
}

bt <- bt_raw |>
  group_by(iso3, year) |>
  summarise(outbreaks = sum(outbreaks, na.rm = TRUE), .groups = "drop")

# Countries and years in the study. A country/year with no row = 0 outbreaks reported.
study_countries <- unique(bt$iso3)
study_years     <- seq(min(bt$year), max(bt$year))

bt_full <- bt |>
  complete(iso3 = study_countries, year = study_years, fill = list(outbreaks = 0))

# ---- 2. Temperature anomalies (Our World in Data, ERA5) --------------------
temp_raw <- read_csv(here("data", "raw", "annual-temperature-anomalies.csv"),
                     show_col_types = FALSE)

# OWID files: Entity, Code, Year, <value>. Rename the value column whatever its label.
temp <- temp_raw |>
  rename(iso3 = Code, year = Year) |>
  mutate(iso3 = if_else(iso3 == "OWID_KOS", "XKX", iso3)) |>   # OWID's code for Kosovo
  rename(temp_anomaly = 4) |>
  filter(!is.na(iso3), nchar(iso3) == 3) |>
  dplyr::select(iso3, year, temp_anomaly)

# ---- 3. Join and check ------------------------------------------------------
panel <- bt_full |>
  left_join(temp, by = c("iso3", "year")) |>
  mutate(country = countrycode(iso3, "iso3c", "country.name",
                               custom_match = c(XKX = "Kosovo")),
         year_c  = year - round(mean(year)),           # centred year for the trend
         # EU Animal Health Law applies from 21 April 2021: ADIS counts drop sharply after it,
         # so reporting regime is treated as a covariate.
         ahl_period = as.integer(year >= 2021))

missing_temp <- panel |> filter(is.na(temp_anomaly))
if (nrow(missing_temp) > 0) {
  warning(nrow(missing_temp), " country-years have no temperature value; check iso3 codes.")
  print(missing_temp)
}

dir.create(here("data", "processed"), recursive = TRUE, showWarnings = FALSE)
write_csv(panel, here("data", "processed", "bt_climate_panel.csv"))
message("Saved panel: ", nrow(panel), " rows, ", length(study_countries), " countries, ",
        min(study_years), "-", max(study_years))
