"""
AEM-EVOLVE Multi-Agent Governance API — In-memory metrics collector.

Tracks per-operation timing for demo benchmarking.
Not persistent, not thread-safe across workers — demo use only.

Usage:
    with metrics.timer("event_creation"):
        ...  # timed block

    metrics.increment("scope_limited")
    data = metrics.snapshot()
"""

from __future__ import annotations

import statistics
import time
from collections import defaultdict
from contextlib import contextmanager
from typing import Iterator


class MetricsRegistry:
    def __init__(self) -> None:
        self._timings: dict[str, list[float]] = defaultdict(list)
        self._counters: dict[str, int] = defaultdict(int)

    @contextmanager
    def timer(self, operation: str) -> Iterator[None]:
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            self._timings[operation].append(elapsed_ms)

    def increment(self, counter: str, n: int = 1) -> None:
        self._counters[counter] += n

    def snapshot(self) -> dict:
        result: dict = {"counters": dict(self._counters), "timings": {}}
        for op, samples in self._timings.items():
            if not samples:
                continue
            result["timings"][op] = {
                "count": len(samples),
                "mean_ms": round(statistics.mean(samples), 3),
                "median_ms": round(statistics.median(samples), 3),
                "min_ms": round(min(samples), 3),
                "max_ms": round(max(samples), 3),
                "p95_ms": round(
                    sorted(samples)[int(len(samples) * 0.95)] if len(samples) > 1 else samples[0],
                    3,
                ),
            }
        # governance overhead ratio: governance time / total e2e time
        if "end_to_end" in self._timings and "governance_gate" in self._timings:
            e2e = statistics.mean(self._timings["end_to_end"]) or 1
            gov = statistics.mean(self._timings["governance_gate"])
            result["governance_overhead_ratio"] = round(gov / e2e, 4)
        # SCOPE_LIMITED vs PASS ratio
        sl = self._counters.get("outcome_scope_limited", 0)
        pa = self._counters.get("outcome_pass", 0)
        fc = self._counters.get("outcome_fail_closed", 0)
        total = sl + pa + fc
        if total:
            result["outcome_distribution"] = {
                "SCOPE_LIMITED": sl,
                "PASS": pa,
                "FAIL_CLOSED": fc,
                "scope_limited_ratio": round(sl / total, 4),
            }
        return result

    def reset(self) -> None:
        self._timings.clear()
        self._counters.clear()


# Module-level singleton
registry = MetricsRegistry()
