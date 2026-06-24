#!/usr/bin/env Rscript
# Bidirectionality sensitivity triage for the HEE -> MH DAG.
# Determines whether the orientation of plausibly-bidirectional edges affects
# the MINIMAL ADJUSTMENT SET for the total effect of HEE on MH.
#
# The canonical DAG is the `rawEdges` array in index.html (the edge list used to
# render the DAG). It is transcribed verbatim below. The canonical file is never
# edited; all perturbations are constructed in memory.

suppressMessages(library(dagitty))

exposure <- "HEE"
outcome  <- "MH"

# ---- Canonical edge list (verbatim from rawEdges in index.html) -------------
edges <- list(
  c("ED","EC"), c("ED","MH"), c("ED","PH"),
  c("EC","HEE"), c("EC","MH"), c("EC","PH"), c("EC","H"), c("EC","T"),
  c("EC","O"), c("EC","P"), c("EC","N"), c("EC","SC"), c("EC","DC"), c("EC","SA"),
  c("U","N"), c("U","P"), c("U","SI"), c("U","EC"), c("U","ED"),
  c("U","HEE"), c("U","SC"), c("U","DC"),
  c("U_AH","N"), c("U_AH","EC"), c("U_AH","ED"), c("U_AH","PH"),
  c("U_AH","T"), c("U_AH","SC"),
  c("N","AP"), c("N","GS"), c("N","A"), c("N","NS"), c("N","H"),
  c("N","NO"), c("N","SC"),
  c("NS","MH"), c("NS","PH"), c("NS","SI"),
  c("NS","SC"), c("NS","SA"),
  c("P","HEE"),
  c("D","MH"), c("D","H"), c("D","O"), c("D","EC"), c("D","ED"),
  c("H","HEE"), c("H","PH"), c("H","IEQ"), c("H","SI"),
  c("T","MH"), c("T","HEE"),
  c("O","IEQ"), c("O","MH"),
  c("C","HEE"), c("C","H"), c("C","MH"), c("C","IEQ"),
  c("AP","MH"), c("AP","PH"), c("AP","IEQ"),
  c("GS","MH"), c("GS","PH"), c("GS","IEQ"), c("GS","AP"),
  c("SI","MH"), c("A","MH"), c("A","PH"),
  c("HEE","IEQ"), c("HEE","NO"),
  c("IEQ","MH"), c("IEQ","PH"),
  c("NO","MH"), c("NO","PH"), c("NO","IEQ"),
  c("SC","MH"), c("SC","SI"), c("SC","SA"),
  c("DC","SI"), c("DC","MH"),
  c("SA","MH"), c("SA","PH"),
  c("PH","MH"),
  c("HEE","FP"), c("EC","FP"), c("C","FP"),
  c("FP","MH"), c("FP","PH"), c("FP","IEQ")
)

# ---- Candidate (uncertain) edges, mapped to real node IDs -------------------
# Each entry: committed orientation src -> tgt as it appears in the canonical DAG.
candidates <- list(
  HEE_EC   = c("EC","HEE"),   # HEE--EconomicCapital  (committed EC -> HEE)
  EC_ED    = c("ED","EC"),    # EconomicCapital--Education (committed ED -> EC)
  EC_P     = c("EC","P"),     # EconomicCapital--PolicyAccess (committed EC -> P)
  EC_MH    = c("EC","MH"),    # EconomicCapital--MH (committed EC -> MH)
  PH_MH    = c("PH","MH"),    # MH--PH (committed PH -> MH)
  SA_MH    = c("SA","MH"),    # SubstanceAbuse--MH (committed SA -> MH)
  SI_MH    = c("SI","MH"),    # Isolation--MH (committed SI -> MH)
  EC_PH    = c("EC","PH")     # PhysicalHealth--EconomicCapital (committed EC -> PH)
)
cand_names <- names(candidates)
k <- length(candidates)

# index of each candidate edge within `edges`
cand_idx <- vapply(candidates, function(e) {
  which(vapply(edges, function(x) identical(x, e), logical(1)))
}, integer(1))
stopifnot(all(cand_idx > 0), length(unique(cand_idx)) == k)

# ---- Build a dagitty model from a directed-edge list + bidirected list -------
build_dag <- function(dir_edges, bidir_edges) {
  d  <- vapply(dir_edges,   function(e) paste0(e[1], " -> ", e[2]), character(1))
  b  <- if (length(bidir_edges))
          vapply(bidir_edges, function(e) paste0(e[1], " <-> ", e[2]), character(1))
        else character(0)
  spec <- paste0("dag { ", paste(c(d, b), collapse = " ; "), " }")
  dagitty(spec)
}

# Format an adjustmentSets result into a stable, sorted string.
fmt_sets <- function(as_obj) {
  if (length(as_obj) == 0) return("")                      # non-identifiable
  setstrs <- vapply(as_obj, function(s) {
    if (length(s) == 0) return("{}")                       # empty set = no adj needed
    paste0("{", paste(sort(s), collapse = ","), "}")
  }, character(1))
  paste(sort(setstrs), collapse = " | ")
}

# ---- Enumerate the full 3^k joint configuration space -----------------------
states <- c("original", "reversed", "latent")
grid <- expand.grid(rep(list(states), k), stringsAsFactors = FALSE)
colnames(grid) <- cand_names
N <- nrow(grid)
cat(sprintf("Enumerating %d configurations (3^%d)...\n", N, k))

results <- data.frame(
  config_id   = integer(N),
  hamming     = integer(N),
  state       = character(N),       # "ok" / "cyclic" / "non-identifiable"
  adj_sets    = character(N),
  stringsAsFactors = FALSE
)
for (j in cand_names) results[[j]] <- character(N)

baseline_str <- NA_character_

for (i in seq_len(N)) {
  cfg <- as.character(grid[i, ])
  names(cfg) <- cand_names

  dir_edges   <- edges
  bidir_edges <- list()
  for (j in seq_len(k)) {
    e  <- candidates[[j]]
    st <- cfg[j]
    if (st == "original") {
      dir_edges[[cand_idx[j]]] <- e
    } else if (st == "reversed") {
      dir_edges[[cand_idx[j]]] <- c(e[2], e[1])
    } else { # latent
      dir_edges[[cand_idx[j]]] <- NA          # mark for removal
      bidir_edges[[length(bidir_edges) + 1]] <- e
    }
  }
  dir_edges <- dir_edges[!vapply(dir_edges, function(x) length(x) == 1 && is.na(x[1]), logical(1))]

  res <- tryCatch({
    g <- build_dag(dir_edges, bidir_edges)
    if (!dagitty::isAcyclic(g)) {
      list(state = "cyclic", sets = NA_character_)
    } else {
      as_obj <- adjustmentSets(g, exposure = exposure, outcome = outcome,
                               type = "minimal", effect = "total")
      if (length(as_obj) == 0) {
        list(state = "non-identifiable", sets = "")
      } else {
        list(state = "ok", sets = fmt_sets(as_obj))
      }
    }
  }, error = function(err) {
    msg <- conditionMessage(err)
    if (grepl("cycl|acyclic|not a DAG", msg, ignore.case = TRUE))
      list(state = "cyclic", sets = NA_character_)
    else
      list(state = paste0("error:", msg), sets = NA_character_)
  })

  results$config_id[i] <- i
  results$hamming[i]   <- sum(cfg != "original")
  results$state[i]     <- res$state
  results$adj_sets[i]  <- ifelse(is.na(res$sets), "", res$sets)
  for (j in cand_names) results[[j]][i] <- cfg[j]

  if (all(cfg == "original")) baseline_str <- res$sets
}

cat("Done.\n")

# ---- Baseline check ----------------------------------------------------------
baseline_row <- which(apply(grid, 1, function(r) all(r == "original")))
cat("\n==== BASELINE (all-original) ====\n")
cat("state:", results$state[baseline_row], "\n")
cat("adjustment set(s):", results$adj_sets[baseline_row], "\n")

# ---- Summaries ---------------------------------------------------------------
ok <- results[results$state == "ok", ]
n_cyclic <- sum(results$state == "cyclic")
n_nonid  <- sum(results$state == "non-identifiable")
n_ok     <- nrow(ok)

cat(sprintf("\nValid (acyclic) configs: %d | cyclic: %d | non-identifiable: %d\n",
            n_ok + n_nonid, n_cyclic, n_nonid))

# (a) distinct minimal adjustment sets among identifiable configs
distinct_sets <- aggregate(config_id ~ adj_sets, data = ok, FUN = length)
colnames(distinct_sets) <- c("adj_sets", "n_configs")
distinct_sets <- distinct_sets[order(-distinct_sets$n_configs), ]
# one example config per distinct set
example_cfg <- sapply(distinct_sets$adj_sets, function(s) {
  r <- ok[ok$adj_sets == s, ][1, ]
  paste(sapply(cand_names, function(j) paste0(j, "=", r[[j]])), collapse = ", ")
})
distinct_sets$example_config <- example_cfg

cat("\n==== DISTINCT minimal adjustment sets (identifiable configs) ====\n")
print(distinct_sets, row.names = FALSE)

# (c) Minimal breaking sets: smallest Hamming distance from all-original whose
#     result differs from baseline (changed set OR non-identifiable).
changed <- results[
  (results$state == "non-identifiable") |
  (results$state == "ok" & results$adj_sets != baseline_str), ]
changed <- changed[results$state[match(changed$config_id, results$config_id)] != "cyclic", ]
min_break_h <- if (nrow(changed)) min(changed$hamming) else NA_integer_
breaking <- changed[changed$hamming == min_break_h, ]

cat(sprintf("\n==== MINIMAL BREAKING SETS (Hamming = %s) ====\n",
            ifelse(is.na(min_break_h), "none", min_break_h)))
if (nrow(breaking)) {
  for (i in seq_len(nrow(breaking))) {
    devs <- sapply(cand_names, function(j) {
      v <- breaking[[j]][i]; if (v != "original") paste0(j, "->", v) else NA
    })
    devs <- devs[!is.na(devs)]
    outcome_lbl <- if (breaking$state[i] == "non-identifiable") "NON-IDENTIFIABLE"
                   else paste0("set=", breaking$adj_sets[i])
    cat(sprintf("  [%s]  %s\n", paste(devs, collapse = " & "), outcome_lbl))
  }
}

# (d) Non-identifiable edge combinations (deviation patterns only)
cat("\n==== NON-IDENTIFIABLE configurations ====\n")
cat("count:", n_nonid, "\n")
if (n_nonid > 0) {
  nonid <- results[results$state == "non-identifiable", ]
  nonid_patterns <- sapply(seq_len(nrow(nonid)), function(i) {
    devs <- sapply(cand_names, function(j) {
      v <- nonid[[j]][i]; if (v != "original") paste0(j, "->", v) else NA
    })
    devs <- devs[!is.na(devs)]
    if (length(devs) == 0) "ALL-ORIGINAL" else paste(devs, collapse = " & ")
  })
  pat_tab <- sort(table(nonid_patterns), decreasing = TRUE)
  # also report by minimal hamming
  cat("minimal Hamming among non-identifiable:", min(nonid$hamming), "\n")
  cat("\nDeviation patterns causing non-identifiability (count):\n")
  for (nm in names(pat_tab)) cat(sprintf("  %3d  %s\n", pat_tab[[nm]], nm))
}

# ---- Save outputs ------------------------------------------------------------
out_csv <- "bidirectionality_sensitivity_results.csv"
write.csv(results, out_csv, row.names = FALSE)
cat("\nWrote", out_csv, "\n")

# Save objects for the markdown-writing step
saveRDS(list(
  results = results, distinct_sets = distinct_sets, baseline_str = baseline_str,
  baseline_state = results$state[baseline_row],
  n_ok = n_ok, n_cyclic = n_cyclic, n_nonid = n_nonid,
  breaking = breaking, min_break_h = min_break_h,
  candidates = candidates, cand_names = cand_names,
  nonid = if (n_nonid > 0) results[results$state == "non-identifiable", ] else NULL
), "bidirectionality_summary.rds")
cat("Wrote bidirectionality_summary.rds\n")
