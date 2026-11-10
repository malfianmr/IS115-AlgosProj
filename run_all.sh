#!/usr/bin/env bash
# Run one policy on all 20 days, then the performance monitor on each log.
# Usage: bash run_all.sh <policy_name>      e.g. bash run_all.sh nearest_neighbour
set -e
POLICY="$1"
if [ -z "$POLICY" ]; then echo "usage: bash run_all.sh <policy_name>"; exit 1; fi
for i in $(seq -w 1 20); do
  DAY="day_0$i"
  python3 -m simulator --policy "solution.policies.$POLICY" \
      --data data --day "$DAY" --output "results/$POLICY/$DAY" > /dev/null
  python3 -m solution.performance_monitor \
      --data data --day "$DAY" --log "results/$POLICY/$DAY/log.txt" > /dev/null
  echo "done $POLICY $DAY"
done
