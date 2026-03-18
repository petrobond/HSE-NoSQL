# Load Testing

Tool: `locust` (Python-native and easy to integrate with this project).

## Scenarios

- read-heavy: student profile and enrollments lookup
- mixed: default weights in `locustfile.py`
- write-heavy: increase `write_enrollment` task weight

## Run

```bash
export MONGO_URI="mongodb://app_user:pass@host:27017/university"
bash tests/load/run_load.sh
python tests/load/plot_results.py
```

Generated artifacts:
- `tests/load/results/baseline_stats.csv`
- `tests/load/results/scaled_stats.csv`
- `tests/load/results/summary.png`

## Metrics to include in report

- Throughput (`Requests/s`)
- Latency (`95%`, optionally `99%`)
- Error rate

