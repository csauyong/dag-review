suppressMessages(library(dagitty))
S <- readRDS("bidirectionality_summary.rds")
res <- S$results
cand <- S$cand_names
baseline <- S$baseline_str

cat("Baseline set string:\n  ", baseline, "\n\n")

# ---- Per-edge marginal (Hamming-1) effect -----------------------------------
cat("==== Per-edge marginal effect (single-edge deviations from all-original) ====\n")
for (j in cand) {
  rows <- res[res$hamming == 1 & res[[j]] != "original", ]
  effs <- sapply(c("reversed","latent"), function(st) {
    r <- rows[rows[[j]] == st, ]
    if (nrow(r) == 0) return(NA)
    if (r$state == "cyclic") return("cyclic")
    if (r$state == "non-identifiable") return("NON-ID")
    if (r$adj_sets == baseline) "unchanged" else "CHANGED"
  })
  cat(sprintf("  %-7s  reversed=%-10s  latent=%-10s\n", j, effs["reversed"], effs["latent"]))
}

# ---- Persistence of the compact baseline set {C,EC,H,T,U} -------------------
compact <- "{C,EC,H,T,U}"
has_compact <- function(s) grepl(compact, s, fixed = TRUE)
ok <- res[res$state == "ok", ]
cat(sprintf("\n==== Persistence of compact set %s ====\n", compact))
cat(sprintf("  valid identifiable configs: %d\n", nrow(ok)))
cat(sprintf("  configs where %s remains A minimal set: %d (%.1f%%)\n",
            compact, sum(has_compact(ok$adj_sets)),
            100*mean(has_compact(ok$adj_sets))))
lost <- ok[!has_compact(ok$adj_sets), ]
cat(sprintf("  configs where it is NOT among minimal sets: %d\n", nrow(lost)))
if (nrow(lost)) {
  cat("  minimal Hamming at which compact set is lost:", min(lost$hamming), "\n")
  lh <- lost[lost$hamming == min(lost$hamming), ]
  cat("  single/low-order deviations that drop the compact set:\n")
  pats <- unique(sapply(seq_len(nrow(lh)), function(i){
    d <- sapply(cand, function(j){ v<-lh[[j]][i]; if(v!="original") paste0(j,"->",v) else NA})
    paste(d[!is.na(d)], collapse=" & ")
  }))
  for (p in head(pats, 30)) cat("    ", p, "\n")
}

# ---- Minimal-Hamming non-identifiable configurations ------------------------
cat("\n==== Minimal-Hamming non-identifiable configs ====\n")
nonid <- res[res$state == "non-identifiable", ]
mh <- min(nonid$hamming)
cat("min Hamming:", mh, "\n")
nm <- nonid[nonid$hamming == mh, ]
for (i in seq_len(nrow(nm))) {
  d <- sapply(cand, function(j){ v<-nm[[j]][i]; if(v!="original") paste0(j,"->",v) else NA})
  cat("  ", paste(d[!is.na(d)], collapse=" & "), "\n")
}
# which candidate edges ever participate in a non-id config, and in what state
cat("\nEdges' involvement in the 486 non-identifiable configs (state freq):\n")
for (j in cand) {
  tb <- table(factor(nonid[[j]], levels=c("original","reversed","latent")))
  cat(sprintf("  %-7s  original=%-4d reversed=%-4d latent=%-4d\n", j, tb[1], tb[2], tb[3]))
}

# ---- Cyclic involvement -----------------------------------------------------
cat("\n==== Cyclic configs: which deviations induce cycles ====\n")
cyc <- res[res$state == "cyclic", ]
cat("total cyclic:", nrow(cyc), "\n")
cat("min Hamming among cyclic:", min(cyc$hamming), "\n")
ch <- cyc[cyc$hamming == min(cyc$hamming), ]
for (i in seq_len(nrow(ch))) {
  d <- sapply(cand, function(j){ v<-ch[[j]][i]; if(v!="original") paste0(j,"->",v) else NA})
  cat("  ", paste(d[!is.na(d)], collapse=" & "), "\n")
}
