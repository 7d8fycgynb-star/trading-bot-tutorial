#!/usr/bin/env bash
# 2denní test — default PAPER (simulace). Pro dry-run exchange: MODE=dry-run
set -euo pipefail
cd "$(dirname "$0")/.."

MODE="${MODE:-paper}"          # paper | dry-run | testnet | live
STRATEGY="${STRATEGY:-sma}"
POLL="${POLL:-300}"            # 5 minut
SYMBOL="${SYMBOL:-BTCUSDT}"
INTERVAL="${INTERVAL:-1h}"
DAYS="${DAYS:-2}"

mkdir -p logs
TS="$(date +%Y%m%d_%H%M%S)"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install -r requirements.txt
else
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

echo "Start 2denního testu: mode=$MODE strategy=$STRATEGY days=$DAYS poll=${POLL}s"
echo "Log: logs/${MODE}_${TS}.log"
echo "Stop: Ctrl+C nebo kill \$(cat logs/${MODE}_${TS}.pid)"

if [[ "$MODE" == "paper" ]]; then
  nohup python bot.py live \
    --strategy "$STRATEGY" \
    --symbol "$SYMBOL" \
    --interval "$INTERVAL" \
    --days "$DAYS" \
    --poll "$POLL" \
    --log "logs/${MODE}_${TS}.log" \
    --state "logs/paper_state.json" \
    > "logs/${MODE}_${TS}.out" 2>&1 &
else
  nohup python bot.py trade \
    --mode "$MODE" \
    --strategy "$STRATEGY" \
    --symbol "$SYMBOL" \
    --interval "$INTERVAL" \
    --days "$DAYS" \
    --poll "$POLL" \
    --quote "${QUOTE:-10}" \
    --log "logs/${MODE}_${TS}.log" \
    --state "logs/trade_state.json" \
    > "logs/${MODE}_${TS}.out" 2>&1 &
fi

echo $! > "logs/${MODE}_${TS}.pid"
echo "PID $(cat "logs/${MODE}_${TS}.pid")"
echo "Sleduj: tail -f logs/${MODE}_${TS}.log"
