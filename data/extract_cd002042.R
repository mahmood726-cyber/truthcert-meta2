# Extract CD002042 mortality data from Pairwise70 R package
#
# Provenance: This script produces data/cd002042_mortality.csv
# from the Pairwise70 package (Cochrane Pairwise Meta-Analysis Dataset).
#
# Prerequisites:
#   install.packages("remotes")
#   remotes::install_github("kzalewski/Pairwise70")

library(Pairwise70)

# Load the CD002042 dataset (transfusion thresholds)
data("CD002042", package = "Pairwise70")

# Analysis 6 = 30-day mortality (main outcome)
mort <- CD002042[CD002042$Outcome == "Mortality: 30-day mortality", ]

# Write CSV with columns matching applied_example_cd002042.py expectations
out <- data.frame(
  Study = mort$Study,
  Study.year = mort$Study.year,
  Experimental.cases = mort$Ee,
  Experimental.N = mort$Ne,
  Control.cases = mort$Ec,
  Control.N = mort$Nc,
  Subgroup = ifelse(is.na(mort$Subgroup), "", mort$Subgroup)
)

write.csv(out, "cd002042_mortality.csv", row.names = FALSE)
cat("Wrote", nrow(out), "rows to cd002042_mortality.csv\n")
