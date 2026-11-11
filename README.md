# IS115 Project: Last-Mile Delivery Dispatch

Our performance metric is **Total Daily Cost** (lower is better):

```
cost = 0.50 x km driven  +  5 x late parcels  +  15 x undelivered parcels
```

Early deliveries are free. The prices are set at the top of `solution/performance_monitor.py`.

Requirements: Python 3.9 or later, standard library only. Run every command from the project root (the folder containing `simulator/`, `data/` and `solution/`).

## Policies

| Policy (module name)    | Idea                                                                  |
|-------------------------|-----------------------------------------------------------------------|
| `baseline`              | Supplied FIFO policy (unchanged)                                      |
| `nearest_neighbour`     | Rule 1: greedy, always drive to the closest location next             |
| `urgent_nearest`        | Rule 2: most urgent parcel (heap) picks the first stop, then Rule 1   |
| `urgent_nearest_2opt`   | Rule 3: Rule 2, then 2-opt local search on the stop order             |
| `zones_strict`          | Rule 4a: each van serves only its own area (areas found with BFS)     |
| `zones_help`            | Rule 4b: as 4a, but an idle van helps the busiest area                |
| `zones_wait_30` ... `zones_wait_100` | Rule 5: as 4b, but a van leaves only when X% full, unless waiting would make a parcel late (recommended: `zones_wait_90`) |

All shared code is in `solution/policies/helpers.py`; each policy file imports only from it.

## Reproduce the results

### 1. One policy, one day

```bash
python3 -m simulator --policy solution.policies.baseline \
    --data data --day day_001 \
    --output results/baseline/day_001

python3 -m solution.performance_monitor \
    --data data --day day_001 \
    --log results/baseline/day_001/log.txt
```

This writes `results/baseline/day_001/log.txt` and `results/baseline/day_001/metrics.json`.
Replace `baseline` with any policy name from the table above.

### 2. One policy, all 20 days

```bash
bash run_all.sh baseline
bash run_all.sh zones_wait_90
```

`run_all.sh` runs the simulator and the performance monitor for `day_001` to `day_020`,
saving each day in `results/<policy>/day_XXX/`.

### 3. Every policy, all 20 days

```bash
for p in baseline nearest_neighbour urgent_nearest urgent_nearest_2opt \
         zones_strict zones_help zones_wait_30 zones_wait_50 zones_wait_60 \
         zones_wait_70 zones_wait_80 zones_wait_90 zones_wait_100; do
  bash run_all.sh "$p"
done
```

On Windows without bash (PowerShell), for one policy:

```powershell
1..20 | ForEach-Object {
  $d = "day_{0:D3}" -f $_
  python -m simulator --policy solution.policies.zones_wait_90 --data data --day $d --output results/zones_wait_90/$d
  python -m solution.performance_monitor --data data --day $d --log results/zones_wait_90/$d/log.txt
}
```

### 4. Summary and analysis tables

```bash
python3 summarize_results.py   # average metrics per policy; writes results/summary.csv
python3 analysis.py            # runtime, day-to-day spread and cost-sensitivity tables
```

`analysis.py` writes `results/analysis_daily.csv`, `results/analysis_runtime.csv` and
`results/analysis_sensitivity.csv`.

## Folder layout

```
simulator/                 supplied simulator (unchanged)
data/                      supplied input data (unchanged)
solution/
  performance_monitor.py   Total Daily Cost metric
  policies/
    baseline.py            supplied policy (unchanged)
    helpers.py             shared helpers for all policies
    <policy>.py            one file per policy
results/<policy>/day_XXX/  log.txt and metrics.json for every policy and day
run_all.sh                 run one policy on all 20 days
summarize_results.py       comparison table
analysis.py                runtime and sensitivity analysis
```
