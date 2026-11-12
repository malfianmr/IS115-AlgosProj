$policies = "baseline", "greedy", "greedy_heap", "greedy_heap_2opt",
            "zones_strict", "zones_help",
            "zones_wait_30", "zones_wait_40", "zones_wait_50", "zones_wait_60",
            "zones_wait_70", "zones_wait_80", "zones_wait_90", "zones_wait_100"

foreach ($p in $policies) {
    foreach ($i in 1..20) {
        $d = "day_{0:D3}" -f $i
        python -m simulator --policy solution.policies.$p --data data --day $d --output results/$p/$d
        python -m solution.performance_monitor --data data --day $d --log results/$p/$d/log.txt
    }
    Write-Host "done $p"
}

python summarize_results.py