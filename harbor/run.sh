#!/usr/bin/env bash
#
# Convenience wrapper: run an Arena Harbor agent on SWE-bench Verified.
#
#   AGENT=stella ARENA_STELLA_BIN=/path/to/linux/stella ./run.sh
#   AGENT=oxagen ARENA_OXAGEN_INSTALL="npm i -g @scope/oxagen" ./run.sh
#   AGENT=byo   ARENA_AGENT_SPEC=$PWD/my-agent.toml ARENA_AGENT_NAME=my ./run.sh
#   AGENT=claude-code ./run.sh          # a Harbor built-in competitor
#
# Prereqs: Docker running; the arena-harbor package installed (pip install -e .);
# a provider API key exported for your chosen model.
set -euo pipefail
cd "$(dirname "$0")"

AGENT="${AGENT:-byo}"
MODEL="${MODEL:-anthropic/claude-sonnet-5}"
DATASET="${DATASET:-swe-bench/swe-bench-verified}"
N_CONCURRENT="${N_CONCURRENT:-4}"
N_ATTEMPTS="${N_ATTEMPTS:-1}"
JOBS_DIR="${JOBS_DIR:-results/$AGENT}"

# Map the friendly AGENT name to a Harbor selector. Arena agents load by import
# path; anything else is treated as a Harbor built-in (claude-code, codex, ...).
case "$AGENT" in
  byo)    AGENT_SEL=(--agent-import-path arena_harbor:ByoAgent) ;;
  oxagen) AGENT_SEL=(--agent-import-path arena_harbor:OxagenAgent) ;;
  stella) AGENT_SEL=(--agent-import-path arena_harbor:StellaAgent) ;;
  *)      AGENT_SEL=(--agent "$AGENT") ;;
esac

# Optional task filter: TASK_IDS="django__django-11099 sympy__sympy-1234"
FILTER=()
for t in ${TASK_IDS:-}; do FILTER+=(--include-task-name "*$t*"); done

echo "== Arena/Harbor run =="
echo "agent=$AGENT  model=$MODEL  dataset=$DATASET  n=$N_CONCURRENT  k=$N_ATTEMPTS"
echo "jobs-dir=$JOBS_DIR"

exec harbor run \
  "${AGENT_SEL[@]}" \
  --dataset "$DATASET" \
  -m "$MODEL" \
  -n "$N_CONCURRENT" \
  -k "$N_ATTEMPTS" \
  -o "$JOBS_DIR" \
  "${FILTER[@]}" \
  ${HARBOR_EXTRA:-}
