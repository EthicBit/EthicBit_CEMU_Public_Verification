"""
Unit tests for MetricsRegistry.
"""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from metrics import MetricsRegistry


@pytest.fixture
def reg():
    return MetricsRegistry()


class TestTimer:
    def test_timer_records_entry(self, reg):
        with reg.timer("op1"):
            time.sleep(0.001)
        assert "op1" in reg._timings
        assert len(reg._timings["op1"]) == 1

    def test_timer_elapsed_positive(self, reg):
        with reg.timer("op2"):
            time.sleep(0.001)
        assert reg._timings["op2"][0] > 0

    def test_timer_accumulates(self, reg):
        for _ in range(3):
            with reg.timer("op3"):
                pass
        assert len(reg._timings["op3"]) == 3

    def test_timer_records_on_exception(self, reg):
        with pytest.raises(ValueError):
            with reg.timer("op_exc"):
                raise ValueError("test")
        assert len(reg._timings["op_exc"]) == 1


class TestIncrement:
    def test_increment_default(self, reg):
        reg.increment("c1")
        assert reg._counters["c1"] == 1

    def test_increment_by_n(self, reg):
        reg.increment("c2", 5)
        assert reg._counters["c2"] == 5

    def test_increment_accumulates(self, reg):
        reg.increment("c3")
        reg.increment("c3")
        reg.increment("c3")
        assert reg._counters["c3"] == 3


class TestSnapshot:
    def test_snapshot_empty(self, reg):
        snap = reg.snapshot()
        assert "counters" in snap
        assert "timings" in snap

    def test_snapshot_has_mean_median(self, reg):
        reg._timings["e2e"].extend([1.0, 2.0, 3.0])
        snap = reg.snapshot()
        assert "e2e" in snap["timings"]
        t = snap["timings"]["e2e"]
        assert t["count"] == 3
        assert t["mean_ms"] == pytest.approx(2.0, rel=1e-3)
        assert t["median_ms"] == pytest.approx(2.0, rel=1e-3)
        assert t["min_ms"] == pytest.approx(1.0)
        assert t["max_ms"] == pytest.approx(3.0)

    def test_snapshot_single_sample_p95(self, reg):
        reg._timings["single"].append(7.5)
        snap = reg.snapshot()
        assert snap["timings"]["single"]["p95_ms"] == pytest.approx(7.5)

    def test_snapshot_outcome_distribution(self, reg):
        reg.increment("outcome_scope_limited", 3)
        reg.increment("outcome_pass", 1)
        snap = reg.snapshot()
        assert "outcome_distribution" in snap
        dist = snap["outcome_distribution"]
        assert dist["SCOPE_LIMITED"] == 3
        assert dist["PASS"] == 1
        assert dist["scope_limited_ratio"] == pytest.approx(0.75)

    def test_snapshot_no_distribution_when_empty(self, reg):
        snap = reg.snapshot()
        assert "outcome_distribution" not in snap

    def test_snapshot_counters_reflected(self, reg):
        reg.increment("sessions_started", 10)
        snap = reg.snapshot()
        assert snap["counters"]["sessions_started"] == 10


class TestReset:
    def test_reset_clears_timings(self, reg):
        reg._timings["x"].append(5.0)
        reg.reset()
        assert len(reg._timings) == 0

    def test_reset_clears_counters(self, reg):
        reg.increment("x", 5)
        reg.reset()
        assert len(reg._counters) == 0
