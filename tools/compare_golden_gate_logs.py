#!/usr/bin/env python3
"""Compare repeatable Henge Golden Gate log samples without modifying guest files.

Usage:
  python3 tools/compare_golden_gate_logs.py baseline1.log baseline2.log --candidate m3_1.log m3_2.log

This intentionally reports only values actually present in the logs; it does not
infer FPS or speedups from elapsed time or claim a benchmark was performed.
"""
import argparse
import re
import statistics
from pathlib import Path

METRICS = {
    "translations": r"\btranslations\s*[:=]\s*(\d+)",
    "block_flushes": r"\bblock_flushes\s*[:=]\s*(\d+)",
    "flush_full": r"\bflush_full\s*[:=]\s*(\d+)",
    "tr_waits": r"\btr_waits\s*[:=]\s*(\d+)",
    "gpu_frames": r"\bgpu_frames\s*[:=]\s*(\d+)",
}

def read_metrics(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    result = {}
    for name, pattern in METRICS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            result[name] = int(matches[-1])
    return result

def summarize(paths):
    samples = [read_metrics(p) for p in paths]
    return {name: statistics.median(s[name] for s in samples if name in s)
            for name in METRICS if any(name in s for s in samples)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", nargs="+", help="Original Henge logs")
    parser.add_argument("--candidate", nargs="+", required=True, help="Optimized Henge logs")
    args = parser.parse_args()
    baseline = summarize(args.baseline)
    candidate = summarize(args.candidate)
    print(f"Baseline files: {len(args.baseline)}; candidate files: {len(args.candidate)}")
    print("These are raw counters, not normalized performance measurements.")
    print(f"{'Counter':20} {'Baseline':>14} {'Candidate':>14} {'Change':>12}")
    for name in METRICS:
        a, b = baseline.get(name), candidate.get(name)
        if a is None or b is None:
            print(f"{name:20} {'missing' if a is None else a:>14} {'missing' if b is None else b:>14} {'n/a':>12}")
        else:
            change = "n/a" if a == 0 else f"{(b/a-1)*100:+.1f}%"
            print(f"{name:20} {a:14g} {b:14g} {change:>12}")
    print("For valid comparisons, use equal workloads and durations; counters alone do not establish faster execution.")

if __name__ == "__main__":
    main()
