# 03_sensitivity.R -- is the temperature effect robust?
# The main model's IRR may be driven by the 2006-2008 BTV-8 epidemic, which coincided
# with very warm years in northern Europe. Each model below removes one possible confounder.
library(tidyverse)
library(glmmTMB)
library(broom.mixed)
library(here)

panel <- read_csv(here("data", "processed", "bt_climate_panel.csv"), show_col_types = FALSE) |>
  group_by(iso3) |>
  arrange(year, .by_group = TRUE) |>
  mutate(temp_anomaly_lag1 = lag(temp_anomaly)) |>   # previous year's anomaly
  ungroup()

fit <- function(formula, data) glmmTMB(formula, family = nbinom2, data = data)

models <- list(
  "1. Main model (2005-2025)" =
    fit(outbreaks ~ temp_anomaly + year_c + ahl_period + (1 | iso3), panel),
  "2. Excluding BTV-8 epidemic (2006-2008)" =
    fit(outbreaks ~ temp_anomaly + year_c + ahl_period + (1 | iso3),
        filter(panel, !year %in% 2006:2008)),
  "3. Before Animal Health Law (2005-2020)" =
    fit(outbreaks ~ temp_anomaly + year_c + (1 | iso3), filter(panel, year <= 2020)),
  "4. Year random effect (Europe-wide shocks)" =
    fit(outbreaks ~ temp_anomaly + ahl_period + (1 | iso3) + (1 | year), panel),
  "5. Previous year's anomaly (lag 1)" =
    fit(outbreaks ~ temp_anomaly_lag1 + year_c + ahl_period + (1 | iso3),
        filter(panel, !is.na(temp_anomaly_lag1)))
)

results <- imap_dfr(models, \(m, name) {
  tidy(m, effects = "fixed", conf.int = TRUE, exponentiate = TRUE) |>
    filter(str_detect(term, "temp_anomaly")) |>
    transmute(model = name, n = nobs(m), IRR = estimate,
              ci_low = conf.low, ci_high = conf.high, p = p.value)
}) |>
  mutate(across(c(IRR, ci_low, ci_high), \(x) round(x, 2)), p = signif(p, 2))

print(results, width = Inf)

dir.create(here("output"), showWarnings = FALSE)
write_csv(results, here("output", "sensitivity_irr.csv"))

# Forest plot of the temperature IRR across models
p <- ggplot(results, aes(IRR, fct_rev(model))) +
  geom_vline(xintercept = 1, linetype = "dashed", colour = "grey50") +
  geom_pointrange(aes(xmin = ci_low, xmax = ci_high), colour = "#2c7fb8") +
  scale_x_log10() +
  labs(x = "Incidence rate ratio per +1 °C anomaly (log scale)", y = NULL,
       title = "Temperature effect on bluetongue outbreaks: sensitivity analyses") +
  theme_minimal(base_size = 11)
ggsave(here("output", "sensitivity_forest.png"), p, width = 8, height = 4, dpi = 200)
p
