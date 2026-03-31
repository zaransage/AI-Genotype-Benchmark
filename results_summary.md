# Genotype Benchmark Results

**Comparison:** Baseline (free-form best practice) vs Genotype (hexagonal architecture, AI_CONTRACT conventions)
**Model:** claude-sonnet-4-6
**Services:** tic_tac_toe · crontab_clone · ui_dashboard
**Runs per variant:** 3
**Phases:** Build (Phase 1/2) → Expand (Phase 4/5)

> **Measurement note:** The genotype variant uses `uv` to manage virtualenvs. In several runs the `.venv` directory was not fully excluded from final `du`/`find` measurements, inflating file counts, size, and LOC in the final measure. Affected cells are marked `†`. The *initial* measure (taken immediately after the build phase, before expand) is the more reliable code metric.
>
> **Completeness:** All 18 runs completed.
>
> **Wall-clock note:** Two expand runs include rate-limit sleep time. `ui_dashboard · baseline · run 2 · expand` wall-clock was 14,831 s (API time ~225 s). `ui_dashboard · genotype · run 3 · expand` wall-clock was 85,078 s (API time 238 s). Per-run tables show API time; wall-clock is noted where it diverges.

---

## 1 · Summary by Service and Variant (averages across 3 runs)

### Build Phase

| Service | Variant | Avg Wall (s) | Avg Cost ($) | Avg Initial Files | Avg Initial LOC | Avg Initial Tests |
|---|---|---:|---:|---:|---:|---:|
| tic_tac_toe | baseline | 69 | 0.156 | 11 | 271 | 18 |
| tic_tac_toe | genotype | 333 | 0.904 | 27 ‡ | 1,010 ‡ | 45 |
| crontab_clone | baseline | 206 | 0.433 | 17 | 502 | 21 |
| crontab_clone | genotype | 370 | 1.084 | 28 ‡ | 1,135 ‡ | 46 |
| ui_dashboard | baseline | 76 | 0.203 | 16 | 433 | 22 |
| ui_dashboard | genotype | 389 | 1.109 | 26 ‡ | 917 ‡ | 49 |

‡ Averages computed only from runs where `.venv` did not inflate the measurement (1–2 clean runs per service).

### Expand Phase

| Service | Variant | Avg Wall (s) | Avg Cost ($) | Avg Final Files | Avg Final LOC | Avg Final Tests |
|---|---|---:|---:|---:|---:|---:|
| tic_tac_toe | baseline | 199 | 0.372 | 17 | 650 | 34 |
| tic_tac_toe | genotype | 478 | 1.275 | — † | — † | 77 |
| crontab_clone | baseline | 287 | 0.559 | 25 | 699 | 35 |
| crontab_clone | genotype | 275 | 0.763 | — † | — † | — † |
| ui_dashboard | baseline | 223 | 0.485 | 23 | 903 | 41 |
| ui_dashboard | genotype | 380 | 1.061 | 67 ‡ | 1,434 ‡ | 81 |

‡ Final files/LOC from run 3 only (runs 1–2 inflated by `.venv`).

### Total Cost per Run (build + expand)

| Service | Baseline Avg ($) | Genotype Avg ($) | Genotype Multiplier |
|---|---:|---:|---:|
| tic_tac_toe | 0.53 | 2.18 | 4.1× |
| crontab_clone | 0.99 | 1.85 | 1.9× |
| ui_dashboard | 0.69 | 2.17 | 3.1× |
| **Overall** | **0.74** | **2.07** | **2.8×** |

---

## 2 · Per-Run Detail — Build Phase

| Service | Run | Variant | Wall (s) | Cost ($) | Input Tok | Output Tok | Files | Size | LOC | Test Files | Test Cases |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| tic_tac_toe | 1 | baseline | 76 | 0.1649 | 14 | 4,330 | 12 | 76K | 262 | 1 | 16 |
| tic_tac_toe | 1 | genotype | 347 | 0.9318 | 32 | 27,821 | 27 | 164K | 1,010 | 3 | 56 |
| tic_tac_toe | 2 | baseline | 59 | 0.1440 | 11 | 4,139 | 12 | 80K | 276 | 1 | 20 |
| tic_tac_toe | 2 | genotype | 355 | 1.0234 | 44 | 24,414 | 40 | 240K | 717 | 3 | 41 |
| tic_tac_toe | 3 | baseline | 71 | 0.1575 | 12 | 4,357 | 10 | 72K | 276 | 1 | 18 |
| tic_tac_toe | 3 | genotype | 296 | 0.7576 | 28 | 21,982 | 734 † | 35M † | 156,574 † | 4 | 38 |
| crontab_clone | 1 | baseline | 259 | 0.5380 | 20 | 19,122 | 22 | 144K | 508 | 1 | 16 |
| crontab_clone | 1 | genotype | 422 | 1.1601 | 50 | 28,396 | 29 | 176K | 1,193 | 3 | 46 |
| crontab_clone | 2 | baseline | 187 | 0.4055 | 18 | 13,715 | 21 | 144K | 522 | 1 | 23 |
| crontab_clone | 2 | genotype | 359 | 1.1580 | 55 | 24,655 | 976 † | 39M † | 172,707 † | 4 | 39 |
| crontab_clone | 3 | baseline | 173 | 0.3562 | 14 | 13,509 | 9 | 44K | 476 | 1 | 25 |
| crontab_clone | 3 | genotype | 328 | 0.9338 | 38 | 24,484 | 27 | 168K | 1,076 | 3 | 53 |
| ui_dashboard | 1 | baseline | 69 | 0.1906 | 13 | 5,776 | 17 | 112K | 408 | 1 | 26 |
| ui_dashboard | 1 | genotype | 531 | 1.5121 | 54 | 35,660 | 985 † | 39M † | 172,913 † | 4 | 50 |
| ui_dashboard | 2 | baseline | 83 | 0.2167 | 16 | 5,930 | 17 | 112K | 415 | 1 | 22 |
| ui_dashboard | 2 | genotype | 301 | 0.8761 | 38 | 22,613 | 26 | 164K | 1,019 | 3 | 67 |
| ui_dashboard | 3 | baseline | 77 | 0.2011 | 14 | 6,081 | 15 | 104K | 475 | 1 | 19 |
| ui_dashboard | 3 | genotype | 335 | 0.9404 | 45 | 21,733 | 26 | 156K | 713 | 3 | 31 |

---

## 3 · Per-Run Detail — Expand Phase

| Service | Run | Variant | Wall (s) | Cost ($) | Input Tok | Output Tok | Files | Size | LOC | Test Files | Test Cases |
|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| tic_tac_toe | 1 | baseline | 206 | 0.4082 | 15 | 14,356 | 19 | 124K | 518 | 2 | 29 |
| tic_tac_toe | 1 | genotype | 610 | 1.6968 | 93 | 45,494 | 55 | 372K | 1,669 | 5 | 89 |
| tic_tac_toe | 2 | baseline | 284 | 0.4824 | 17 | 16,441 | 18 | 152K | 747 | 2 | 39 |
| tic_tac_toe | 2 | genotype | 413 | 1.1065 | 72 | 29,456 | 1,009 † | 39M † | 173,195 † | 6 | 79 |
| tic_tac_toe | 3 | baseline | 108 | 0.2243 | 9 | 7,801 | 13 | 120K | 686 | 2 | 33 |
| tic_tac_toe | 3 | genotype | 410 | 1.0207 | 96 | 30,498 | 990 † | 39M † | 173,096 † | 6 | 63 |
| crontab_clone | 1 | baseline | 295 | 0.5557 | 45 | 19,471 | 25 | 172K | 621 | 2 | 27 |
| crontab_clone | 1 | genotype | 312 | 0.9179 | 78 | 22,949 | 1,056 † | 41M † | 188,091 † | 12 | 287 |
| crontab_clone | 2 | baseline | 140 | 0.2967 | 49 | 10,242 | 23 | 172K | 621 | 2 | 36 |
| crontab_clone | 2 | genotype | 236 | 0.6093 | 76 | 20,136 | 982 † | 39M † | 173,228 † | 4 | 61 |
| crontab_clone | 3 | baseline | 427 | 0.8235 | 38 | 29,519 | 28 | 180K | 854 | 3 | 43 |
| crontab_clone | 3 | genotype | 277 | 0.7620 | 27 | 17,479 | 987 † | 39M † | 173,399 † | 6 | 79 |
| ui_dashboard | 1 | baseline | 196 | 0.4412 | 52 | 15,391 | 24 | 208K | 974 | 3 | 52 |
| ui_dashboard | 1 | genotype | 435 | 1.1579 | 100 | 32,680 | 999 † | 39M † | 173,594 † | 6 | 79 |
| ui_dashboard | 2 | baseline | 225 * | 0.4822 | 39 | 16,845 | 23 | 188K | 844 | 2 | 33 |
| ui_dashboard | 2 | genotype | 468 | 1.1670 | 64 | 41,334 | 986 † | 39M † | 173,671 † | 6 | 111 |
| ui_dashboard | 3 | baseline | 249 | 0.5308 | 15 | 19,394 | 21 | 192K | 890 | 2 | 38 |
| ui_dashboard | 3 | genotype | 238 * | 0.8590 | 32 | 20,274 | 67 | 452K | 1,434 | 5 | 53 |

\* Actual API duration; wall-clock was 85,078 s due to a rate-limit sleep. `ui_dashboard · baseline · run 2 · expand` API time was ~225 s; wall-clock was 14,831 s.

---

## 4 · Token Usage Comparison

Input tokens shown are non-cached (`input_tokens` field). Both variants make heavy use of the prompt cache; total effective context is much larger (reflected in cost).

### Output Tokens by Phase

| Service | Variant | Build Out Tok (avg) | Expand Out Tok (avg) | Total Out Tok (avg) |
|---|---|---:|---:|---:|
| tic_tac_toe | baseline | 4,275 | 12,866 | 17,141 |
| tic_tac_toe | genotype | 24,739 | 35,149 | 59,888 |
| crontab_clone | baseline | 15,449 | 19,744 | 35,193 |
| crontab_clone | genotype | 25,845 | 20,188 | 46,033 |
| ui_dashboard | baseline | 5,929 | 17,210 | 23,139 |
| ui_dashboard | genotype | 26,669 | 31,429 | 58,098 |

---

## 5 · Code Quality: Test Coverage

| Service | Run | Variant | Initial Test Cases | Final Test Cases | Tests Added |
|---|---|---|---:|---:|---:|
| tic_tac_toe | 1 | baseline | 16 | 29 | +13 |
| tic_tac_toe | 1 | genotype | 56 | 89 | +33 |
| tic_tac_toe | 2 | baseline | 20 | 39 | +19 |
| tic_tac_toe | 2 | genotype | 41 | 79 | +38 |
| tic_tac_toe | 3 | baseline | 18 | 33 | +15 |
| tic_tac_toe | 3 | genotype | 38 | 63 | +25 |
| crontab_clone | 1 | baseline | 16 | 27 | +11 |
| crontab_clone | 1 | genotype | 46 | 287 | +241 |
| crontab_clone | 2 | baseline | 23 | 36 | +13 |
| crontab_clone | 2 | genotype | 39 | 61 | +22 |
| crontab_clone | 3 | baseline | 25 | 43 | +18 |
| crontab_clone | 3 | genotype | 53 | 79 | +26 |
| ui_dashboard | 1 | baseline | 26 | 52 | +26 |
| ui_dashboard | 1 | genotype | 50 | 79 | +29 |
| ui_dashboard | 2 | baseline | 22 | 33 | +11 |
| ui_dashboard | 2 | genotype | 67 | 111 | +44 |
| ui_dashboard | 3 | baseline | 19 | 38 | +19 |
| ui_dashboard | 3 | genotype | 31 | 53 | +22 |

### Average Test Cases (clean runs only)

| Service | Baseline Initial | Baseline Final | Genotype Initial | Genotype Final |
|---|---:|---:|---:|---:|
| tic_tac_toe | 18 | 34 | 45 | 77 |
| crontab_clone | 21 | 35 | 46 | — ‡ |
| ui_dashboard | 22 | 41 | 49 | 81 |

‡ crontab_clone run 1 genotype expand produced 287 tests (possible over-generation outlier).

---

## 6 · Genotype LOC (clean runs only)

Rows marked † above have inflated metrics due to `.venv` inclusion. The following table shows only runs where the initial measurement was not inflated:

| Service | Run | Initial Files | Initial LOC | Final Files | Final LOC |
|---|---|---:|---:|---:|---:|
| tic_tac_toe | 1 | 27 | 1,010 | 55 | 1,669 |
| tic_tac_toe | 2 | 40 | 717 | † | † |
| crontab_clone | 1 | 29 | 1,193 | † | † |
| crontab_clone | 3 | 27 | 1,076 | † | † |
| ui_dashboard | 2 | 26 | 1,019 | † | † |
| ui_dashboard | 3 | 26 | 713 | 67 | 1,434 |

---

## 7 · Final Repository Sizes (on disk, `.venv` excluded)

Measured from each output directory after all phases completed.

| Service | Run | Baseline | Genotype |
|---|---|---:|---:|
| tic_tac_toe | 1 | 124K | 372K |
| tic_tac_toe | 2 | 152K | 536K |
| tic_tac_toe | 3 | 120K | 408K |
| **tic_tac_toe avg** | | **132K** | **439K** |
| crontab_clone | 1 | 172K | 424K |
| crontab_clone | 2 | 172K | 336K |
| crontab_clone | 3 | 180K | 428K |
| **crontab_clone avg** | | **175K** | **396K** |
| ui_dashboard | 1 | 208K | 480K |
| ui_dashboard | 2 | 188K | 404K |
| ui_dashboard | 3 | 192K | 348K |
| **ui_dashboard avg** | | **196K** | **411K** |

### Size Multiplier (genotype / baseline)

| Service | Baseline Avg | Genotype Avg | Multiplier |
|---|---:|---:|---:|
| tic_tac_toe | 132K | 439K | 3.3× |
| crontab_clone | 175K | 396K | 2.3× |
| ui_dashboard | 196K | 411K | 2.1× |
| **Overall** | **168K** | **415K** | **2.5×** |

---

## 8 · Known Confounds and Limitations

| # | Issue | Impact |
|---|---|---|
| 1 | `.venv` inflation | `uv` installs ~960 files / ~39 MB into a `.venv` that evades the exclusion filters in several runs. File count, size, and LOC in those final measures are unusable. |
| 2 | Global `~/.claude/CLAUDE.md` | Loaded on all runs (OAuth auth requires normal startup). Baseline reflects "Claude with user global config", not a pristine agent. |
| 3 | Rate-limit sleeps included in wall-clock | `ui_dashboard · baseline · run 2 · expand` shows 14,831 s wall-clock (actual API time: 225 s). |
| 4 | No test execution | Tests are counted but not run; passing rate is unknown. |
