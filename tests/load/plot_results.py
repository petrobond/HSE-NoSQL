#!/usr/bin/env python3
"""Plot throughput and p95 latency from Locust CSV exports."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def load_case(case_prefix: Path) -> tuple[float, float]:
    stats_path = case_prefix.with_name(case_prefix.name + "_stats.csv")
    if not stats_path.exists():
        raise FileNotFoundError(f"Cannot find {stats_path}")

    df = pd.read_csv(stats_path)
    total = df[df["Name"] == "Aggregated"]
    if total.empty:
        raise RuntimeError(f"'Aggregated' row not found in {stats_path}")

    row = total.iloc[0]
    rps = float(row["Requests/s"])
    p95 = float(row["95%"])
    return rps, p95


def main() -> None:
    parser = argparse.ArgumentParser(description="Build load test charts from Locust CSV")
    parser.add_argument("--baseline-prefix", default="tests/load/results/baseline")
    parser.add_argument("--scaled-prefix", default="tests/load/results/scaled")
    parser.add_argument("--out-dir", default="tests/load/results")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cases = {
        "baseline": Path(args.baseline_prefix),
        "scaled": Path(args.scaled_prefix),
    }

    labels = []
    rps_values = []
    p95_values = []
    for label, prefix in cases.items():
        rps, p95 = load_case(prefix)
        labels.append(label)
        rps_values.append(rps)
        p95_values.append(p95)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].bar(labels, rps_values)
    axes[0].set_title("Throughput (Requests/s)")
    axes[0].set_ylabel("RPS")

    axes[1].bar(labels, p95_values)
    axes[1].set_title("Latency p95 (ms)")
    axes[1].set_ylabel("ms")

    plt.tight_layout()
    output = out_dir / "summary.png"
    plt.savefig(output, dpi=140)
    print(f"Saved chart to {output}")


if __name__ == "__main__":
    main()

