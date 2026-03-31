#!/bin/bash
# =============================================================================
# Test + Coverage Runner
# Runs pytest with coverage against all 18 benchmark output directories.
# Uses uv for fast venv creation and dependency installation.
#
# Usage: bash run_tests.sh
# Output: test_results_YYYYMMDD_HHMMSS.log
# =============================================================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG="$(pwd)/test_results_${TIMESTAMP}.log"
SERVICES=("tic_tac_toe" "crontab_clone" "ui_dashboard")
VARIANTS=("baseline" "genotype")
EXTRA_DEPS="pytest pytest-cov httpx"

log() { echo "$1" | tee -a "$LOG"; }

run_dir_tests() {
  local dir="$1"
  local label="$2"
  local abs_dir
  abs_dir="$(realpath "$dir")"

  if [ ! -d "$abs_dir" ]; then
    log "  SKIP $label — directory not found"
    return
  fi

  log ""
  log "──────────────────────────────────────────"
  log "DIR  $label"

  local venv_dir="$abs_dir/.venv"
  local pytest_bin="$venv_dir/bin/pytest"

  # Create venv — force python3 to bypass pyproject.toml requires-python constraints
  uv venv "$venv_dir" --python python3 --quiet 2>>"$LOG"
  if [ ! -f "$pytest_bin" ]; then
    # venv exists but pytest not installed yet; this is fine, will install below
    :
  fi
  if [ ! -d "$venv_dir" ]; then
    log "  ERROR could not create venv for $label"
    return
  fi

  # Install from requirements.txt if present
  if [ -f "$abs_dir/requirements.txt" ]; then
    uv pip install --quiet --python "$venv_dir/bin/python" \
      -r "$abs_dir/requirements.txt" 2>>"$LOG"
  fi

  # Always ensure pytest, pytest-cov, httpx are present
  uv pip install --quiet --python "$venv_dir/bin/python" $EXTRA_DEPS 2>>"$LOG"

  if [ ! -f "$pytest_bin" ]; then
    log "  ERROR pytest not found after install for $label"
    return
  fi

  # Run pytest with coverage from inside the directory
  local output
  output=$(cd "$abs_dir" && "$pytest_bin" \
    --tb=short \
    --cov=. \
    --cov-report=term-missing \
    -q \
    --ignore=.venv \
    2>&1)

  echo "$output" >> "$LOG"

  # Parse summary line (last line with pass/fail counts)
  local summary
  summary=$(echo "$output" | grep -E "[0-9]+ passed|[0-9]+ failed|[0-9]+ error|no tests ran" | tail -1)
  [ -z "$summary" ] && summary="no output"

  # Parse coverage total
  local coverage
  coverage=$(echo "$output" | grep "^TOTAL" | awk '{print $NF}')
  [ -z "$coverage" ] && coverage="n/a"

  log "  RESULT   ${summary}"
  log "  COVERAGE ${coverage}"
}

log "======================================================================"
log "Test + Coverage Run  started: $(date -Iseconds)"
log "======================================================================"

for service in "${SERVICES[@]}"; do
  for run in 1 2 3; do
    for variant in "${VARIANTS[@]}"; do
      dir="$(pwd)/${variant}_${service}_${run}"
      label="${variant}/${service}/run${run}"
      run_dir_tests "$dir" "$label"
    done
  done
done

log ""
log "======================================================================"
log "Test + Coverage Run  finished: $(date -Iseconds)"
log "Results: $LOG"
log "======================================================================"
