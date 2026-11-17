# 00_setup.R -- install and load the packages used in the project
# Run once: source("R/00_setup.R")

pkgs <- c("tidyverse", "countrycode", "sf", "rnaturalearth", "rnaturalearthdata",
          "MASS", "glmmTMB", "DHARMa", "broom", "broom.mixed", "here")

to_install <- setdiff(pkgs, rownames(installed.packages()))
if (length(to_install) > 0) install.packages(to_install)

# Load only what the scripts need globally. MASS is NOT attached: its select()
# would mask dplyr::select(). It is called as MASS::glm.nb() instead.
invisible(lapply(setdiff(pkgs, "MASS"), library, character.only = TRUE))
