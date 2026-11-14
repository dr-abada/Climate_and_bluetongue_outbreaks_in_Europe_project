# 02_models.R -- count models of bluetongue outbreaks vs temperature anomaly
library(tidyverse)
library(MASS)       # glm.nb
library(glmmTMB)    # mixed models for counts
library(DHARMa)     # residual checks for GLMMs
library(here)

panel <- read_csv(here("data", "processed", "bt_climate_panel.csv"), show_col_types = FALSE)

# ---- 1. Poisson GLM: baseline, usually over-dispersed for outbreak counts ---
m_pois <- glm(outbreaks ~ temp_anomaly + year_c + ahl_period, family = poisson, data = panel)
dispersion <- sum(residuals(m_pois, type = "pearson")^2) / df.residual(m_pois)
message("Poisson dispersion ratio: ", round(dispersion, 1), " (>1 means over-dispersion)")

# ---- 2. Negative-binomial GLM ----------------------------------------------
m_nb <- MASS::glm.nb(outbreaks ~ temp_anomaly + year_c + ahl_period, data = panel)

# ---- 3. Negative-binomial GLMM with a country random intercept -------------
# The random effect absorbs stable country differences (herd size, surveillance, reporting).
m_nbmm <- glmmTMB(outbreaks ~ temp_anomaly + year_c + ahl_period + (1 | iso3),
                  family = nbinom2, data = panel)

# ---- 4. Compare and check ---------------------------------------------------
print(AIC(m_pois, m_nb, m_nbmm))
print(summary(m_nbmm))

# Incidence rate ratio: multiplicative change in outbreaks per +1 °C anomaly
irr <- exp(fixef(m_nbmm)$cond["temp_anomaly"])
message("IRR per +1 °C anomaly: ", round(irr, 2))

sim <- simulateResiduals(m_nbmm)
png(here("output", "dharma_residuals.png"), width = 1400, height = 700, res = 150)
plot(sim)
dev.off()

saveRDS(list(pois = m_pois, nb = m_nb, nbmm = m_nbmm), here("output", "models.rds"))
