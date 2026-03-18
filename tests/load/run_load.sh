#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${MONGO_URI:-}" ]]; then
  echo "MONGO_URI env var is required"
  exit 1
fi

mkdir -p tests/load/results

# Baseline: low users
locust -f tests/load/locustfile.py \
  --headless \
  --users 20 \
  --spawn-rate 5 \
  --run-time 2m \
  --csv tests/load/results/baseline \
  --only-summary

# Scaled: medium users
locust -f tests/load/locustfile.py \
  --headless \
  --users 80 \
  --spawn-rate 10 \
  --run-time 2m \
  --csv tests/load/results/scaled \
  --only-summary

