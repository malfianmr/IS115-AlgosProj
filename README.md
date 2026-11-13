# IS115 Project: Last-Mile Delivery Dispatch

**Group:** G3T4
**Members:** Muhammad Alfian bin Mohammed Rizal, Bramsha Akheel Thaha

## Performance metric

**Total Daily Cost** (lower is better):

```
cost = 0.50 x km driven + 5 x late parcels + 15 x undelivered parcels
```

Early deliveries are not penalised, as we assume customers are happy when their parcel comes early and it still arrives.
The metric is implemented in `solution/performance_monitor.py`.

## Policies

| Policy | Idea |
|---|---|
| `baseline` | Supplied policy (unchanged) |
| `greedy` | Always drive to the closest location next |
| `greedy_heap` | Start at the most urgent location (heap), then closest next |
| `greedy_heap_2opt` | `greedy_heap`, then shorten the route with 2-opt |
| `zones_strict` | Each van only serves its own zone (zones found with BFS) |
| `zones_help` | `zones_strict`, but a van with an empty zone helps the busiest zone |
| `zones_wait_30` ... `zones_wait_100` | `zones_help`, but a van only leaves when 30–100% full, unless waiting would make a parcel late |

**Recommended policy:** `zones_wait_90`

Shared code is in `solution/policies/helpers.py`.

### Run one policy for one day

```
python -m simulator --policy solution.policies.example --data data --day day_001 --output results/example/day_001
```

### Run the performance monitor on that day

```
python -m solution.performance_monitor --data data --day day_001 --log results/example/day_001/log.txt
```

This writes `log.txt` and `metrics.json` to `results/example/day_001/`.
Replace `example` with any policy name above, and `day_001` with any day from `day_001` to `day_020`.

### Run everything

```
python run_all_and_summarize.py
```

This runs every policy on all 20 days, saves the results in `results/<policy>/day_XXX/`,
and writes the average results of each policy to `all_policies_summary.csv`.