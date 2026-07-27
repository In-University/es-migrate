#!/usr/bin/env bash
#:USAGE
#
# Runs es_rollback_py.sh once per index, in sequence.
#
# es_rollback_py.sh deliberately knows about one index only: one state
# directory, one journal, one lock, one set of counters. Everything about
# "which indices, in what order, and what to do when one fails" lives here
# instead, where it is fifteen lines of shell rather than a second control
# flow threaded through a thousand.
#
# Sequential on purpose. The delta sync already fans out across shards, and
# ES6 is disk-bound during a rollback; a second index running concurrently
# competes for the same spindle and makes both slower.
#
# One index failing does not stop the rest -- every index is attempted, and
# the summary at the end says which ones need attention. That matters for an
# overnight run: a bad mapping on one index should not cost you the window
# for the other nine.
#
# Usage:
#   ./es_rollback_all.sh <command> [index ...]
#
#   Passed through to es_rollback_py.sh, once per index:
#     preflight   checks only, writes nothing
#     run         start a fresh run
#     resume      continue an interrupted run
#     status      show phase and counters
#     verify      re-run phase 4 on its own
#     undo        restore ES6 from the journal
#     reset       drop state (keeps the journal)
#
#   Handled here, without touching a cluster:
#     summary     print the state table for every index
#
#   Naming one or more indices limits the run to those; with none, every
#   index in INDEX_TS runs in sorted order.
#
# Examples:
#   ./es_rollback_all.sh preflight            # checks only, every index
#   ./es_rollback_all.sh run                  # the real thing
#   ./es_rollback_all.sh resume orders        # retry just the one that failed
#   ./es_rollback_all.sh summary              # where did everything end up
#   ./es_rollback_all.sh undo products
#
# Env: everything es_rollback_py.sh accepts (ES6_URL, ES9_URL, ELASTIC_PW,
# PAGE_SIZE, ASSUME_YES, ...) is inherited untouched. Two extra:
#
#   STATE_ROOT   parent of the per-index state dirs (default ./.rollback-state)
#   ROLLBACK_SH  path to the single-index script (default alongside this one)
#
# Exit codes, worst across all indices:
#   0 ok | 1 fatal | 2 finished with dead letters | 130 interrupted
#
#:END-USAGE

# Not `set -e`: a non-zero exit from one index is data for the summary, not
# a reason to abandon the remaining indices.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROLLBACK_SH="${ROLLBACK_SH:-$HERE/es_rollback_py.sh}"
STATE_ROOT="${STATE_ROOT:-./.rollback-state}"

# ------------------------------------------------------------------ config --
# Index -> the field a write on that index bumps. The name is the same on
# both clusters (both sides address the alias, e.g. products -> products_v1.0.1),
# so one key covers source and target.
#
# The Jenkins pipeline keeps its own copy of this list and does not call this
# script. That is deliberate: this is the by-hand path on the VM, Jenkins is
# the automated one, and neither should stop working because the other moved.
# The cost is remembering to add a new index in both places.
declare -A INDEX_TS=(
  [products]=updated_at
  [orders]=system_update_at
)

# ---------------------------------------------------------------------------

usage() { sed -n '/^#:USAGE$/,/^#:END-USAGE$/{ /^#:/d; s/^# \{0,1\}//; p; }' "$0"; exit 1; }
fail()  { printf 'FATAL %s\n' "$*" >&2; exit 1; }

CMD="${1:-}"; shift || true
[ -n "$CMD" ] || usage
case "$CMD" in
  preflight|run|resume|status|verify|undo|reset|summary) ;;
  *) fail "unknown command: $CMD" ;;
esac

# Bash iterates an associative array in hash order, which would shuffle the
# log and the summary between runs for no reason. Sort the keys.
ALL=()
mapfile -t ALL < <(printf '%s\n' "${!INDEX_TS[@]}" | sort)

# A named index that is not in the map is a typo, and a typo that silently
# did nothing would read as "that index had no work to do".
INDICES=()
if [ "$#" -eq 0 ]; then
  INDICES=("${ALL[@]}")
else
  for want in "$@"; do
    [ -n "${INDEX_TS[$want]:-}" ] || fail "'$want' is not in INDEX_TS (have: ${ALL[*]})"
    INDICES+=("$want")
  done
fi

# --------------------------------------------------------------- reporting --

# Severity ladder for the process exit code: a fatal on any index outranks an
# interrupt, which outranks dead letters, which outranks success. The worst
# outcome is the one worth acting on.
severity()   { case "$1" in 0) echo 0 ;; 2) echo 1 ;; 130) echo 2 ;; *) echo 3 ;; esac; }
worst_code() { case "$1" in 0) echo 0 ;; 1) echo 2 ;; 2) echo 130 ;; *) echo 1 ;; esac; }
label()      { case "$1" in 0) echo OK ;; 2) echo DEADLETTER ;; 130) echo INTERRUPTED ;; *) echo FAILED ;; esac; }

# One value out of a state.env. Values are counters and phase names, so a
# plain cut is enough; -f2- keeps anything with an = in it intact.
sv() {
  local v
  v="$(grep -m1 "^$2=" "$1" 2>/dev/null | cut -d= -f2-)"
  printf '%s' "${v:-$3}"
}

# RC_OF is filled by the run loop and empty when `summary` is invoked on its
# own, which is what lets one table serve both. A dash means "this command
# did not run that index", not "it succeeded".
declare -A RC_OF=()

summary() {
  local idx s rc
  printf '\n%-24s %-16s %18s %9s %9s %11s  %s\n' \
    INDEX PHASE SEEN/SYNCED DELETED REPAIRED DEADLETTER RESULT
  for idx in "${INDICES[@]}"; do
    s="$STATE_ROOT/$idx/state.env"
    rc="${RC_OF[$idx]:-}"
    printf '%-24s %-16s %18s %9s %9s %11s  %s\n' \
      "$idx" \
      "$(sv "$s" PHASE none)" \
      "$(sv "$s" SEEN 0)/$(sv "$s" SYNCED 0)" \
      "$(sv "$s" DELETED -)" \
      "$(sv "$s" REPAIRED -)" \
      "$(sv "$s" DL_COUNT 0)" \
      "${rc:+$(label "$rc")}${rc:--}"
  done
  printf '\nstate: %s/<index>/   dead letters: %s/<index>/deadletter.ndjson\n\n' \
    "$STATE_ROOT" "$STATE_ROOT"
}

if [ "$CMD" = "summary" ]; then
  summary
  exit 0
fi

# -------------------------------------------------------------------- run --

[ -f "$ROLLBACK_SH" ] || fail "cannot find $ROLLBACK_SH"

WORST=0
for idx in "${INDICES[@]}"; do
  ts="${INDEX_TS[$idx]}"
  printf '\n========== %s: %s (delta on %s) ==========\n' "$CMD" "$idx" "$ts"

  SRC_INDEX="$idx" DST_INDEX="$idx" TS_FIELD="$ts" \
  STATE_DIR="$STATE_ROOT/$idx" \
    bash "$ROLLBACK_SH" "$CMD"
  rc=$?

  RC_OF["$idx"]="$rc"
  s="$(severity "$rc")"; [ "$s" -le "$WORST" ] || WORST="$s"

  # An interrupt is the operator asking to stop, not a per-index failure --
  # honour it instead of starting the next index.
  if [ "$rc" -eq 130 ]; then
    printf '\n>> interrupted; not starting the remaining index(es)\n' >&2
    break
  fi
  [ "$rc" -eq 0 ] || printf '\n>> %s finished with rc=%d (%s) -- continuing\n' \
    "$idx" "$rc" "$(label "$rc")" >&2
done

printf '\n========== summary (%s) ==========' "$CMD"
summary

exit "$(worst_code "$WORST")"
