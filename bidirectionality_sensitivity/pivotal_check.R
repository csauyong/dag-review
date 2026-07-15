S <- readRDS("bidirectionality_summary.rds")
res <- S$results
cand <- S$cand_names

# Outcome label per config: cyclic / nonid / the adj_sets string
res$outcome <- ifelse(res$state == "cyclic", "<cyclic>",
                ifelse(res$state == "non-identifiable", "<non-id>", res$adj_sets))

cat("==== Pivotality test ====\n")
cat("For each candidate edge: holding the other 7 fixed, does changing THIS edge's\n")
cat("state ever change the outcome (adjustment set / identifiability)?\n")
cat("'free dimension' = never pivotal across all 3^7 contexts.\n\n")

for (j in cand) {
  others <- setdiff(cand, j)
  key <- apply(res[, others], 1, paste, collapse="|")
  # within each context, count distinct outcomes
  pivotal_ctx <- 0; total_ctx <- 0
  # also: pivotal ignoring cyclic (orientation/latent among VALID graphs only)
  pivotal_valid <- 0
  for (g in split(seq_len(nrow(res)), key)) {
    total_ctx <- total_ctx + 1
    outs <- res$outcome[g]
    if (length(unique(outs)) > 1) pivotal_ctx <- pivotal_ctx + 1
    valid <- outs[outs != "<cyclic>"]
    if (length(unique(valid)) > 1) pivotal_valid <- pivotal_valid + 1
  }
  cat(sprintf("  %-7s pivotal in %4d/%d contexts (incl. cyclic) | %4d/%d among valid-only\n",
              j, pivotal_ctx, total_ctx, pivotal_valid, total_ctx))
}
