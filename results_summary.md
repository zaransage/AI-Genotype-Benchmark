# Genotype Benchmark Results

**Comparison:** Baseline (free-form best practice) vs Genotype (hexagonal architecture, AI_CONTRACT conventions)
**Model:** claude-sonnet-4-6
**Services:** tic_tac_toe · crontab_clone · ui_dashboard
**Runs per variant:** 3 per service (18 total)
**Phases:** Build (REST API) → Expand (web UI + SQLite persistence)
**Test execution:** All 18 runs verified — 100% pass rate across both variants

---

## Key Findings

| Metric | Baseline | Genotype | Ratio |
|---|---:|---:|---:|
| Avg cost per full run | $0.74 | $2.07 | **2.8×** |
| Avg build time | 117 s | 364 s | **3.1×** |
| Avg final LOC (post-expand) | ~700 | ~1,580 | **2.3×** |
| Avg final test cases (pytest) | 37 | 76 | **2.1×** |
| Avg test coverage | 97% | 95% | −2 pp |
| Expand cost overhead vs build | 2.0× | **1.1×** | genotype cheaper |
| Structural consistency (9 runs) | ❌ varies | ✅ identical | |

**Bottom line:** Genotype costs ~3× more and takes ~3× longer to build. In return you get ~2× more tests, consistent architecture across every run, and expand phases that are dramatically cheaper relative to build — suggesting the hexagonal structure reduces the model's re-reasoning cost when making changes.

---

## Methodology

Each service was built from a single prompt in two variants:

- **Baseline** — "Build a production-ready REST API using Python best practices." No architectural constraints. The model chooses structure freely.
- **Genotype** — Same functional requirement plus a hexagonal architecture contract (ports/adaptors, `domain/` tree, `fixtures/`, `uv` tooling). Convention enforced via the Agentic-Code-Genotype prompt library.

Each run proceeded in two phases:
1. **Build** — initial API generated from scratch; measured immediately after.
2. **Expand** — add a web UI and SQLite persistence to the existing API; measured after.

Metrics captured: wall-clock duration, API cost (via Claude Code token billing), file count, LOC, test file count, test case count (grep `def test_`), disk size. All measurements exclude `.venv`, `__pycache__`, and `*.pyc`. Test execution used `pytest --cov` in a fresh `uv` environment.

---

## 1 · Summary by Service and Variant

### 1a · Build Phase (averages across 3 runs)

| Service | Variant | Avg Time (s) | Avg Cost ($) | Avg Files | Avg LOC | Avg Test Cases |
|---|---|---:|---:|---:|---:|---:|
| tic_tac_toe | baseline | 69 | 0.156 | 11 | 271 | 18 |
| tic_tac_toe | genotype | 333 | 0.904 | 27 | 1,010 | 45 |
| crontab_clone | baseline | 206 | 0.433 | 17 | 502 | 21 |
| crontab_clone | genotype | 370 | 1.084 | 28 | 1,135 | 46 |
| ui_dashboard | baseline | 76 | 0.203 | 16 | 433 | 22 |
| ui_dashboard | genotype | 389 | 1.109 | 26 | 917 | 49 |

> Build-phase genotype averages exclude runs where `.venv` inflated measurements (see §11).

### 1b · Expand Phase (averages across 3 runs)

| Service | Variant | Avg Time (s) | Avg Cost ($) | Avg Files | Avg LOC | Avg Test Cases |
|---|---|---:|---:|---:|---:|---:|
| tic_tac_toe | baseline | 199 | 0.372 | 17 | 650 | 34 |
| tic_tac_toe | genotype | 478 | 1.275 | 55 ‡ | 1,669 ‡ | 77 |
| crontab_clone | baseline | 287 | 0.559 | 25 | 699 | 35 |
| crontab_clone | genotype | 275 | 0.763 | — † | — † | 71 |
| ui_dashboard | baseline | 223 | 0.485 | 23 | 903 | 41 |
| ui_dashboard | genotype | 380 | 1.061 | 67 ‡ | 1,434 ‡ | 81 |

† All expand-phase genotype file/LOC/size measurements for crontab_clone were inflated by `.venv`. Test counts are unaffected.
‡ Average from clean runs only (1–2 per service).

### 1c · Total Cost per Full Run

| Service | Baseline ($) | Genotype ($) | Ratio |
|---|---:|---:|---:|
| tic_tac_toe | 0.53 | 2.18 | 4.1× |
| crontab_clone | 0.99 | 1.85 | 1.9× |
| ui_dashboard | 0.69 | 2.17 | 3.1× |
| **Overall** | **0.74** | **2.07** | **2.8×** |

### 1d · Clean Final-State Metrics (post-all-phases, .venv excluded)

The following are re-measured from the current repository state using `find` and `wc -l` with full `.venv`/`__pycache__` exclusion. These directories have also received Expansion 2 work (auth, retry, time-series) and are therefore higher than the original expand-phase measurements.

| Service | Variant | Files | LOC | Test Fns | Size |
|---|---|---:|---:|---:|---:|
| tic_tac_toe | baseline | 12 | 2,006 | 87 | 216K |
| tic_tac_toe | genotype | 60 | 4,238 | 184 | 615K |
| crontab_clone | baseline | 15 | 2,283 | 109 | 236K |
| crontab_clone | genotype | 29 | 2,980 | 125 | 365K |
| ui_dashboard | baseline | 14 | 2,510 | 103 | 280K |
| ui_dashboard | genotype | 33 | 3,491 | 163 | 421K |

| | Files ratio | LOC ratio | Test ratio | Size ratio |
|---|---:|---:|---:|---:|
| tic_tac_toe | 5.1× | 2.1× | 2.1× | 2.8× |
| crontab_clone | 2.0× | 1.3× | 1.1× | 1.5× |
| ui_dashboard | 2.4× | 1.4× | 1.6× | 1.5× |
| **Overall** | **3.0×** | **1.6×** | **1.6×** | **1.9×** |

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

† `.venv` was included in this measurement. File count, size, and LOC are unusable. Test case counts are unaffected.

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
| crontab_clone | 1 | genotype | 312 | 0.9179 | 78 | 22,949 | 1,056 † | 41M † | 188,091 † | 12 | 74 |
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

† `.venv` included in measurement; file/size/LOC unusable. Test counts unaffected.
\* API duration; wall-clock was inflated by a rate-limit sleep. `ui_dashboard · genotype · run 3 · expand` wall-clock was 85,078 s. `ui_dashboard · baseline · run 2 · expand` API time ~225 s; wall-clock 14,831 s.

> **Correction vs original log:** `crontab_clone · genotype · run 1 · expand` was logged as 287 test cases via `grep "def test_"`. `pytest` executed 74. The discrepancy was due to parametrized test expansion being over-counted by grep. The 74 figure is used here and throughout.

---

## 4 · Token Usage

Input tokens shown are non-cached (`input_tokens` field). Both variants make heavy use of the prompt cache; total effective context is much larger (reflected in cost). Output tokens drive the majority of the cost difference.

### Output Tokens by Phase

| Service | Variant | Build Out Tok (avg) | Expand Out Tok (avg) | Total Out Tok (avg) | Ratio |
|---|---|---:|---:|---:|---:|
| tic_tac_toe | baseline | 4,275 | 12,866 | 17,141 | — |
| tic_tac_toe | genotype | 24,739 | 35,149 | 59,888 | **3.5×** |
| crontab_clone | baseline | 15,449 | 19,744 | 35,193 | — |
| crontab_clone | genotype | 25,845 | 20,188 | 46,033 | **1.3×** |
| ui_dashboard | baseline | 5,929 | 17,210 | 23,139 | — |
| ui_dashboard | genotype | 26,669 | 31,429 | 58,098 | **2.5×** |

Output token ratio directly explains the cost ratio. Genotype produces more code, more tests, and more structured boilerplate — all of which translate to more output tokens. The model also emits longer reasoning traces when following explicit architectural contracts.

---

## 5 · Test Coverage

All 18 runs executed with `pytest --cov` in a fresh `uv` environment. `.venv` excluded from coverage. **Every run achieved 100% pass rate.** Neither variant produced a failing test suite.

### Per-Run Results

| Service | Run | Variant | Tests Passed | Coverage |
|---|---|---|---:|---:|
| tic_tac_toe | 1 | baseline | 29 | 99% |
| tic_tac_toe | 1 | genotype | 89 | 94% |
| tic_tac_toe | 2 | baseline | 39 | 100% |
| tic_tac_toe | 2 | genotype | 79 | 98% |
| tic_tac_toe | 3 | baseline | 40 | 100% |
| tic_tac_toe | 3 | genotype | 63 | 92% |
| crontab_clone | 1 | baseline | 27 | 95% |
| crontab_clone | 1 | genotype | 74 | 95% |
| crontab_clone | 2 | baseline | 36 | 92% |
| crontab_clone | 2 | genotype | 61 | 97% |
| crontab_clone | 3 | baseline | 43 | 98% |
| crontab_clone | 3 | genotype | 79 | 97% |
| ui_dashboard | 1 | baseline | 52 | 99% |
| ui_dashboard | 1 | genotype | 79 | 96% |
| ui_dashboard | 2 | baseline | 33 | 95% |
| ui_dashboard | 2 | genotype | 111 | 95% |
| ui_dashboard | 3 | baseline | 38 | 98% |
| ui_dashboard | 3 | genotype | 53 | 90% |

### Averages by Service

| Service | Baseline Tests | Baseline Cov | Genotype Tests | Genotype Cov | Test Ratio |
|---|---:|---:|---:|---:|---:|
| tic_tac_toe | 36 | 100% | 77 | 95% | **2.1×** |
| crontab_clone | 35 | 95% | 71 | 96% | **2.0×** |
| ui_dashboard | 41 | 97% | 81 | 94% | **2.0×** |
| **Overall** | **37** | **97%** | **76** | **95%** | **2.1×** |

### Test Growth (build → expand)

| Service | Variant | Build Tests | Expand Tests | Tests Added | Growth |
|---|---|---:|---:|---:|---:|
| tic_tac_toe | baseline | 18 | 34 | +16 | 1.9× |
| tic_tac_toe | genotype | 45 | 77 | +32 | 1.7× |
| crontab_clone | baseline | 21 | 35 | +14 | 1.7× |
| crontab_clone | genotype | 46 | 71 | +25 | 1.5× |
| ui_dashboard | baseline | 22 | 41 | +19 | 1.9× |
| ui_dashboard | genotype | 49 | 81 | +32 | 1.7× |

Both variants grew their test suites proportionally during the expand phase. Genotype started with ~2× more tests and maintained that ratio after expansion. Coverage remained comparable (−2 pp on average for genotype), meaning the extra tests are covering additional real code paths introduced by the more granular layer structure, not just padding.

---

## 6 · Structural Consistency

### 6a · Genotype: identical layout across all 9 runs

Top-level structure produced in **every genotype run, every service**:

```
domain/   fixtures/   tests/   main.py   pyproject.toml   requirements.txt   uv.lock
```

Internal `domain` tree was consistent across all 9 runs:

```
domain/
  <service_name>/
    core/
      adaptors/   (inbound — HTTP routes, web UI)
      ports/      (outbound — in-memory store, SQLite)
```

The only inter-run variation was a naming choice for the intermediate module (`core` / `game` / `scheduler` / `dashboard`) — a label, not a structural deviation.

### 6b · Baseline: different layout every run

| Run | tic_tac_toe | crontab_clone | ui_dashboard |
|---|---|---|---|
| 1 | flat files + `static/` + `conftest.py` | `tests/` + `templates/` + split modules | `tests/` + flat modules |
| 2 | flat files, no subdirs | `tests/` + split modules | `tests/` + `templates/` |
| 3 | flat files, no subdirs | `tests/` + `templates/` + 4 modules | flat test files + `templates/` |

No two baseline runs of the same service produced the same layout. Baseline services share only `main.py`, `requirements.txt`, and `README.md`. Module names, test placement, and folder layout were reinvented each time.

### 6c · Cross-service similarity

A developer opening any genotype service sees the same directory structure regardless of which service it is. The `domain/adaptors/ports` split, `fixtures/` contract files, and `tests/<service>/test_*.py` layout are identical across all three services.

**Practical implication:** In a multi-service codebase, genotype's consistency reduces onboarding cost and makes cross-service tooling (linters, CI templates, shared test runners, code generation) immediately feasible. Baseline produces bespoke outputs that don't compose.

---

## 7 · Change Efficiency (Expand vs Build)

The expand phase added a web UI and SQLite persistence to a working API — a realistic incremental change task. The ratio below shows how much more expensive the expand phase was relative to the build phase.

| Service | Baseline time ratio | Genotype time ratio | Baseline cost ratio | Genotype cost ratio |
|---|---:|---:|---:|---:|
| tic_tac_toe | 2.9× | 1.4× | 2.4× | 1.4× |
| crontab_clone | 1.4× | **0.74×** | 1.3× | **0.70×** |
| ui_dashboard | 2.9× | **0.97×** | 2.4× | **0.96×** |
| **Average** | **2.4×** | **1.0×** | **2.0×** | **1.1×** |

Baseline expand phases cost 2–3× more than their build phases. Genotype expand phases cost roughly the same as the initial build — and for crontab_clone and ui_dashboard were actually *cheaper*.

This is the clearest practical signal in the data. Once the hexagonal structure exists, the model locates the correct insertion points quickly: a new inbound adaptor for the web UI, a new outbound port for SQLite. It does less re-reading of the whole codebase and less re-reasoning about where code should live. The architectural contract functions as a pre-computed answer to "where does this go?"

---

## 8 · Tradeoffs

### 8a · Costs and benefits summary

| Dimension | Baseline wins | Genotype wins |
|---|---|---|
| Initial speed | ✅ 3× faster build | |
| Initial cost | ✅ 2.8× cheaper | |
| Test count | | ✅ 2.1× more tests |
| Test coverage | ✅ slightly higher (97% vs 95%) | |
| Structural consistency | | ✅ identical across all runs |
| Change cost (expand) | | ✅ proportionally cheaper (1.1× vs 2.0×) |
| Cross-service composability | | ✅ shared tooling immediately feasible |
| Onboarding a new developer | | ✅ one layout to learn, not N |
| Short one-off services | ✅ done faster, costs less | |
| Long-lived or multi-service repos | | ✅ lower total cost of ownership |

### 8b · When genotype is worth it

The upfront cost premium of genotype (~2.8×) is likely recovered when:

- The service will need **2+ expand rounds** (expand costs ~1× for genotype vs 2× for baseline, so the premium amortises quickly)
- You are building **multiple services** that need to share CI configuration, linters, or test runners
- **Onboarding cost matters** — a new developer or agent can navigate any service using the same mental map
- **Test reliability matters** — 2× more tests at equivalent coverage gives more regression confidence per code change

Baseline is the better choice when:

- The service is a **prototype or one-off** unlikely to outlive its first build
- **Speed to first result** is the primary objective
- The team has **no plans for multiple related services** where consistency would compound

### 8c · The hidden cost of inconsistency

Baseline's 3× file ratio advantage (12 files vs 33–60) understates its structural complexity. Because no two baseline runs produce the same layout, tooling must be re-invented per service — separate CI templates, different import structures, varying test discovery configs. For N services, baseline's apparent simplicity multiplies into N bespoke configurations. Genotype's overhead is paid once and shared.

---

## 9 · Repository Sizes

Two measurements per directory:
- **On-disk** — `du` after all phases, `.venv` excluded, `__pycache__`/`.pyc` included
- **Clone size** — `.venv`, `__pycache__`, `*.pyc` all excluded (represents a fresh `git clone`)

| Service | Run | Baseline on-disk | Baseline clone | Genotype on-disk | Genotype clone |
|---|---|---:|---:|---:|---:|
| tic_tac_toe | 1 | 124K | 136K | 372K | 320K |
| tic_tac_toe | 2 | 152K | 152K | 536K | 360K |
| tic_tac_toe | 3 | 120K | 140K | 408K | 328K |
| **tic_tac_toe avg** | | **132K** | **143K** | **439K** | **336K** |
| crontab_clone | 1 | 172K | 168K | 424K | 300K |
| crontab_clone | 2 | 172K | 160K | 336K | 260K |
| crontab_clone | 3 | 180K | 160K | 428K | 336K |
| **crontab_clone avg** | | **175K** | **163K** | **396K** | **299K** |
| ui_dashboard | 1 | 208K | 176K | 480K | 364K |
| ui_dashboard | 2 | 188K | 184K | 404K | 296K |
| ui_dashboard | 3 | 192K | 184K | 348K | 280K |
| **ui_dashboard avg** | | **196K** | **181K** | **411K** | **313K** |

| Service | On-disk ratio | Clone ratio |
|---|---:|---:|
| tic_tac_toe | 3.3× | 2.4× |
| crontab_clone | 2.3× | 1.8× |
| ui_dashboard | 2.1× | 1.7× |
| **Overall** | **2.5×** | **2.0×** |

`__pycache__` generated during test runs accounts for most of the gap between on-disk and clone measurements. The true committed codebase is approximately **2× larger** for genotype than baseline.

---

## 10 · Future Work

### 10a · More models

All runs used `claude-sonnet-4-6`. The genotype hypothesis is architectural, not model-specific, but the magnitude of the effect likely varies by model capability. High-priority candidates:

| Model | Hypothesis |
|---|---|
| Claude Opus 4.6 | Stronger reasoning may reduce genotype build overhead while preserving consistency |
| Claude Haiku 4.5 | Smaller/faster model — does the constraint help or hurt more when reasoning is limited? |
| GPT-4o | Cross-vendor comparison; does hexagonal architecture convention transfer across model families? |
| Gemini 1.5 Pro / 2.0 | Larger context window may change expand-phase cost dynamics |
| Open-weight (Llama 3, Mistral) | Can structured prompting compensate for capability gaps in smaller open models? |

### 10b · More languages

Python + FastAPI was chosen for ecosystem familiarity. Repeating with:

- **TypeScript / Node.js** — genotype conventions exist for TS; different module system
- **Go** — strong typing and package conventions may narrow the genotype benefit
- **Rust** — explicit ownership forces structure regardless of prompt; useful null hypothesis
- **Java / Spring** — already opinionated frameworks; test if genotype adds value on top

Cross-language results would show whether the benefit is Python-specific or architectural.

### 10c · More service types

The three services (game API, job scheduler, metrics dashboard) share REST + CRUD characteristics. Expand to:

- **Event-driven / message queue services** — ports/adaptors pattern is theoretically strongest here
- **ML serving APIs** — different change patterns (model swaps, schema drift)
- **CLI tools** — no HTTP layer; tests architectural flexibility of the pattern
- **Stateful long-running services** — expand phases more structurally complex

### 10d · Functional correctness

Tests passing does not mean the service is correct. Future runs should include:

- **Integration tests** against a running server (`curl`-level smoke tests, Appium/Playwright for web UI)
- **Contract testing** — does the API match a shared OpenAPI spec?
- **Mutation testing** — how many tests actually catch injected bugs? (Measures test *quality*, not just count)
- **Static analysis** — mypy, ruff, bandit scores per variant

This would determine whether genotype's 2× test count translates to 2× defect detection.

### 10e · DB swap / abstraction cost

A separate phase was run testing SQLite → PostgreSQL → DuckDB migrations. Preliminary results showed genotype Phase A (DB abstraction) required 0 files changed (the port interface already existed) vs baseline requiring ~2 files / ~300 LOC of refactoring. Full analysis of this phase should be written up as a companion section.

### 10f · Cost optimisation

The genotype premium (2.8×) comes primarily from output tokens. Future experiments:

- Can a **two-pass approach** (scaffold structure first, fill in logic second) reduce cost?
- Does providing **example genotype code** in context reduce the model's generation overhead?
- Does **prompt compression** of the architectural contract reduce input tokens without losing consistency?
- Is there a **minimal viable constraint** — fewer rules than the full genotype spec — that captures most of the consistency benefit at lower cost?

### 10g · Longitudinal / multi-round study

This benchmark ran 2 phases. Real services go through N rounds of change. A longer study would:

- Run 5–10 sequential expand rounds per service
- Track whether genotype's expand cost advantage compounds (lower total cost over time) or degrades (accumulated context makes changes harder for both variants)
- Measure **developer intervention rate** — how often does a human need to correct the generated code

---

## 11 · Known Confounds and Limitations

| # | Issue | Impact | Status |
|---|---|---|---|
| 1 | `.venv` inflation | `uv` installed ~960 files / ~39 MB into `.venv` that escaped exclusion filters in 11 of 18 expand-phase genotype measurements. File count, size, and LOC in those cells are unusable. Test counts were unaffected. | Documented with † markers. Clean runs and re-measured final state used for all averages. |
| 2 | Global `~/.claude/CLAUDE.md` loaded on all runs | OAuth auth requires normal startup; `--bare` flag was not available without an API key. Baseline reflects "Claude with user global config", not a pristine agent. | Documented. Effect direction unclear. Both variants equally affected. |
| 3 | Rate-limit sleeps in wall-clock | Two expand runs include multi-hour rate-limit sleep in wall-clock time. API duration is the valid measure. | Marked with \* in tables. API time used in all averages. |
| 4 | Small N | 3 replicates per cell. Variance is visible (e.g., tic_tac_toe genotype expand test counts: 89, 79, 63). | Means are directionally reliable but not statistically significant at conventional thresholds. |
| 5 | Single model | All runs on claude-sonnet-4-6. Results may not generalise across models or versions. | See Future Work §10a. |
| 6 | No human quality review | Code was not reviewed for correctness, security, or maintainability beyond test pass rates. | Planned for next phase. |
