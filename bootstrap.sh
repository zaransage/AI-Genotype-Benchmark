#!/bin/bash
# =============================================================================
# Genotype Benchmark — Baseline vs Genotype Comparison
#
# Runs each service 3 times in two conditions:
#   baseline  — free-form best practice, no genotype conventions passed
#   genotype  — hexagonal architecture per ~/git/Agentic-Code-Genotype-main
#
# Each run is fully isolated: separate directory, no session carry-over.
#
# AUTH: Uses your logged-in Claude Code Pro session (keychain/OAuth).
#       No ANTHROPIC_API_KEY required.
#
# LIMITATION: ~/.claude/CLAUDE.md loads on all runs (including baseline) because
#             keychain auth requires normal startup. Baseline therefore reflects
#             "Claude with your global config" rather than a pristine agent.
#             Document this in your paper as a known confound.
#
# SELF-HEALING: If a rate limit is detected the script sleeps until the next
#               3am ET reset and automatically retries (up to 5 attempts).
#
# PREREQ: jq recommended for token extraction from JSON output.
#
# Usage: bash bootstrap.sh
# =============================================================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS="results_${TIMESTAMP}.log"
GENOTYPE_PATH="$HOME/git/Agentic-Code-Genotype-main"
SERVICES=("tic_tac_toe" "crontab_clone" "ui_dashboard")
SLEEP_BETWEEN_SERVICES=1500   # 25 min between service groups

# ── Preflight ─────────────────────────────────────────────────────────────────
if [ ! -d "$GENOTYPE_PATH" ]; then
  echo "ERROR: Genotype path not found: $GENOTYPE_PATH"; exit 1
fi
if ! command -v jq &>/dev/null; then
  echo "WARNING: jq not found — token counts will not be extracted."
fi

# ── Core helpers ──────────────────────────────────────────────────────────────
log() { echo "$1" | tee -a "$RESULTS"; }

measure_dir() {
  local dir="$1" label="$2"
  local file_count size loc test_files test_cases
  # Exclude .venv, __pycache__, and *.pyc so venv installs don't skew counts
  file_count=$(find "$dir" -type f \
    -not -path '*/.venv/*' -not -path '*/__pycache__/*' -not -name '*.pyc' \
    2>/dev/null | wc -l | tr -d ' ')
  size=$(du -sh --exclude='.venv' "$dir" 2>/dev/null | cut -f1 || \
         du -sh "$dir" 2>/dev/null | cut -f1)
  loc=$(find "$dir" -name '*.py' \
    -not -path '*/.venv/*' -not -path '*/__pycache__/*' \
    -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
  test_files=$(find "$dir" \( -name 'test_*.py' -o -name '*_test.py' \) \
    -not -path '*/.venv/*' 2>/dev/null | wc -l | tr -d ' ')
  test_cases=$(grep -r --include="*.py" --exclude-dir='.venv' \
    "def test_" "$dir" 2>/dev/null | wc -l | tr -d ' ')
  log "  [$label] files=${file_count}  size=${size}  loc=${loc:-0}  test_files=${test_files}  test_cases=${test_cases}"
}

extract_tokens() {
  local json_output="$1"
  if command -v jq &>/dev/null; then
    local inp out
    inp=$(echo "$json_output" | jq -r '.usage.input_tokens  // "?"' 2>/dev/null | tail -1)
    out=$(echo "$json_output" | jq -r '.usage.output_tokens // "?"' 2>/dev/null | tail -1)
    echo "tokens_in=${inp}  tokens_out=${out}"
  else
    echo "tokens=unavailable(no jq)"
  fi
}

# Sleep until the next 3am Eastern Time reset (+ 2 min buffer)
sleep_until_reset() {
  local now reset_epoch sleep_secs
  now=$(date +%s)
  # Try GNU date first, then BSD date (macOS)
  reset_epoch=$(TZ="America/New_York" date -d "tomorrow 03:02" +%s 2>/dev/null) || \
  reset_epoch=$(TZ="America/New_York" date -v+1d -j -f "%H:%M" "03:02" +%s 2>/dev/null) || \
  reset_epoch=$(( now + 3600 ))   # fallback: 1 hour
  sleep_secs=$(( reset_epoch - now ))
  [ $sleep_secs -lt 60 ] && sleep_secs=3600
  log "  >> Sleeping ${sleep_secs}s until ~3:02am ET reset ($(date -d "@${reset_epoch}" 2>/dev/null || date -r "${reset_epoch}" 2>/dev/null))..."
  sleep "$sleep_secs"
}

# Run a claude phase with auto-retry on rate limit.
# Usage: run_phase <working_dir> <extra_claude_args> <prompt_string>
# Stores output in global RAW_OUTPUT.
run_phase() {
  local run_dir="$1"
  local extra_args="$2"
  local prompt="$3"
  local max_attempts=5 attempt=0 output=""

  while [ $attempt -lt $max_attempts ]; do
    # shellcheck disable=SC2086
    output=$(cd "$run_dir" && claude \
      --dangerously-skip-permissions \
      --output-format json \
      --no-session-persistence \
      $extra_args \
      -p "$prompt" 2>&1)

    if echo "$output" | grep -qiE "hit your limit|usage limit|rate.?limit|upgrade.*plan|claude\.ai/upgrade"; then
      attempt=$(( attempt + 1 ))
      log "  !! Rate limit detected (attempt ${attempt}/${max_attempts})."
      if [ $attempt -lt $max_attempts ]; then
        sleep_until_reset
      else
        log "  !! Max retries reached — moving on. Output may be empty."
      fi
    else
      RAW_OUTPUT="$output"
      return 0
    fi
  done

  RAW_OUTPUT="$output"
  return 1
}

# ── Service metadata ───────────────────────────────────────────────────────────
service_description() {
  case "$1" in
    tic_tac_toe)   echo "two-player tic-tac-toe game. The API must support: creating a new game, making a move, getting current game state, and determining win/loss/draw." ;;
    crontab_clone) echo "job scheduler (crontab clone). The API must support: creating a scheduled job (name, command, cron expression), listing all jobs, deleting a job, viewing a job's run history, and manually triggering a job." ;;
    ui_dashboard)  echo "metrics dashboard. The API must support: creating a dashboard, adding metric widgets to a dashboard, listing all dashboards, posting a new metric value to a widget, and reading current widget values." ;;
  esac
}

service_expansion() {
  case "$1" in
    tic_tac_toe)   printf '%s\n' "1. A simple web UI (HTML served from the same server) that lets a user play a game in the browser." "2. A SQLite database to persist completed games with their move history and outcome." ;;
    crontab_clone) printf '%s\n' "1. A simple web UI (HTML served from the same server) that displays scheduled jobs and their run history." "2. A SQLite database to persist jobs and run history across restarts." ;;
    ui_dashboard)  printf '%s\n' "1. A simple web UI (HTML served from the same server) that renders dashboards and their widget values." "2. A SQLite database to persist dashboards, widgets, and metric readings." ;;
  esac
}

# =============================================================================
# MAIN LOOP
# =============================================================================
log "======================================================================"
log "Genotype Benchmark  started: $(date -Iseconds)"
log "Services: ${SERVICES[*]}  |  Runs: 3  |  Results: $RESULTS"
log "======================================================================"

first_service=true

for service in "${SERVICES[@]}"; do
  DESC=$(service_description "$service")
  EXPAND=$(service_expansion "$service")

  if [ "$first_service" = true ]; then
    first_service=false
  else
    log ""
    log "── Sleeping ${SLEEP_BETWEEN_SERVICES}s before ${service} to protect rate limit ──"
    sleep "$SLEEP_BETWEEN_SERVICES"
  fi

  for run in 1 2 3; do
    BASELINE_DIR="./baseline_${service}_${run}"
    GENOTYPE_DIR="./genotype_${service}_${run}"

    # Skip if both dirs are already populated
    b_files=$(find "$BASELINE_DIR" -type f 2>/dev/null | wc -l)
    g_files=$(find "$GENOTYPE_DIR" -type f 2>/dev/null | wc -l)
    if [ "$b_files" -gt 2 ] && [ "$g_files" -gt 2 ]; then
      log "SKIP  service=${service}  run=${run}  (already complete)"
      continue
    fi

    log ""
    log "════════════════════════════════════════════════════════════════"
    log "service=${service}  run=${run}  started=$(date -Iseconds)"

    mkdir -p "$BASELINE_DIR" "$GENOTYPE_DIR"

    # ── BASELINE Phase 1: build ───────────────────────────────────────
    log "BASELINE  phase=1_build  dir=${BASELINE_DIR}"
    start=$(date +%s)
    run_phase "$BASELINE_DIR" "" \
"You are a general-purpose coding assistant running in isolation.
Do NOT read, reference, or apply any CLAUDE.md, AGENTS.md, AI_CONTRACT.md, or other
agent config files. Use whatever structure, layout, and approach you personally judge
to be best practice.

Build a REST API in Python for a ${DESC}
Place all files in the current working directory.

Requirements:
- FastAPI + uvicorn
- pytest unit tests
- requirements.txt
- README.md

When every file is written, output ONLY this block and then stop:
REPORT
  start_time: <ISO>
  end_time:   <ISO>
  duration_s: <N>
  files_created: <N>
  python_loc: <N>
END_REPORT"
    end=$(date +%s)
    echo "$RAW_OUTPUT" >> "$RESULTS"
    log "  wall_clock=$((end - start))s  $(extract_tokens "$RAW_OUTPUT")"

    # ── BASELINE Phase 3: measure initial ────────────────────────────
    log "BASELINE  phase=3_measure_initial"
    measure_dir "$BASELINE_DIR" "baseline_initial"

    # ── BASELINE Phase 4: expand ──────────────────────────────────────
    log "BASELINE  phase=4_expand  started=$(date -Iseconds)"
    start=$(date +%s)
    run_phase "$BASELINE_DIR" "" \
"You are a general-purpose coding assistant running in isolation.
Do NOT read, reference, or apply any CLAUDE.md, AGENTS.md, or other agent config files.
Do NOT look outside the current directory.

Expand the existing REST API in the current directory by adding:
${EXPAND}

Rules:
- Do not remove or modify any existing tests.
- Add new tests covering the new features.
- Update requirements.txt if new dependencies are needed.

When every file is written, output ONLY this block and then stop:
REPORT
  start_time:     <ISO>
  end_time:       <ISO>
  duration_s:     <N>
  files_added:    <N>
  files_modified: <N>
  loc_added:      <N>
END_REPORT"
    end=$(date +%s)
    echo "$RAW_OUTPUT" >> "$RESULTS"
    log "  wall_clock=$((end - start))s  $(extract_tokens "$RAW_OUTPUT")"

    # ── BASELINE Phase 6: measure final ──────────────────────────────
    log "BASELINE  phase=6_measure_final"
    measure_dir "$BASELINE_DIR" "baseline_final"

    # ── GENOTYPE Phase 2: build ───────────────────────────────────────
    log "GENOTYPE  phase=2_build  dir=${GENOTYPE_DIR}"
    start=$(date +%s)
    run_phase "$GENOTYPE_DIR" "--add-dir \"$GENOTYPE_PATH\"" \
"Before writing any code, read these genotype files in order:
1. ${GENOTYPE_PATH}/AGENTS.md
2. ${GENOTYPE_PATH}/AI_CONTRACT.md
3. Every ADR in ${GENOTYPE_PATH}/docs/adr/
4. ${GENOTYPE_PATH}/agent-overrides/claude.local.md

Following those conventions exactly, build a REST API in Python for a ${DESC}
Place all files in the current working directory.

Requirements:
- Apply the hexagonal folder layout from AGENTS.md
- FastAPI + uvicorn
- Tests FIRST using unittest (as required by AI_CONTRACT.md)
- uv for all tooling (venv, install, run)
- Write README.md and Mermaid architecture diagram before writing code

When every file is written, output ONLY this block and then stop:
REPORT
  start_time: <ISO>
  end_time:   <ISO>
  duration_s: <N>
  files_created: <N>
  python_loc: <N>
END_REPORT"
    end=$(date +%s)
    echo "$RAW_OUTPUT" >> "$RESULTS"
    log "  wall_clock=$((end - start))s  $(extract_tokens "$RAW_OUTPUT")"

    # ── GENOTYPE Phase 3: measure initial ────────────────────────────
    log "GENOTYPE  phase=3_measure_initial"
    measure_dir "$GENOTYPE_DIR" "genotype_initial"

    # ── GENOTYPE Phase 5: expand ──────────────────────────────────────
    log "GENOTYPE  phase=5_expand  started=$(date -Iseconds)"
    start=$(date +%s)
    run_phase "$GENOTYPE_DIR" "--add-dir \"$GENOTYPE_PATH\"" \
"Re-read ${GENOTYPE_PATH}/AGENTS.md and ${GENOTYPE_PATH}/AI_CONTRACT.md to
refresh the hexagonal conventions.

Expand the existing genotype-structured REST API in the current directory by adding:
${EXPAND}

Architecture guidance:
- Web UI       → new inbound adaptor  (domain/adaptors/)
- SQLite layer → new outbound port    (domain/ports/)
- Wire them in main.py only

Rules:
- Do not remove or modify any existing tests.
- Add new unittest tests covering the new features.
- Use uv for tooling.

When every file is written, output ONLY this block and then stop:
REPORT
  start_time:     <ISO>
  end_time:       <ISO>
  duration_s:     <N>
  files_added:    <N>
  files_modified: <N>
  loc_added:      <N>
END_REPORT"
    end=$(date +%s)
    echo "$RAW_OUTPUT" >> "$RESULTS"
    log "  wall_clock=$((end - start))s  $(extract_tokens "$RAW_OUTPUT")"

    # ── GENOTYPE Phase 6: measure final ──────────────────────────────
    log "GENOTYPE  phase=6_measure_final"
    measure_dir "$GENOTYPE_DIR" "genotype_final"

    log "DONE  service=${service}  run=${run}  finished=$(date -Iseconds)"
  done
done

log ""
log "======================================================================"
log "Genotype Benchmark  finished: $(date -Iseconds)"
log "Results: $RESULTS"
log "======================================================================"
