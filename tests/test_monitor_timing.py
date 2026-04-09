import os
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "mpp_solar"))

from mpp_solar_monitor import MPPSolarMonitor  # noqa: E402


class MonitorTimingTests(unittest.TestCase):
    def setUp(self):
        self._env = os.environ.copy()
        os.environ["INTERVAL"] = "5"

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._env)

    def test_compute_cycle_sleep_subtracts_elapsed_time(self):
        monitor = MPPSolarMonitor()

        sleep_for = monitor.compute_cycle_sleep(100.0, 103.2)

        self.assertAlmostEqual(sleep_for, 1.8, places=2)

    def test_compute_cycle_sleep_returns_zero_when_cycle_is_slow(self):
        monitor = MPPSolarMonitor()

        sleep_for = monitor.compute_cycle_sleep(100.0, 108.5)

        self.assertEqual(sleep_for, 0.0)

    def test_read_deadline_is_capped_for_low_latency_updates(self):
        monitor = MPPSolarMonitor()

        self.assertLessEqual(monitor.get_read_deadline_seconds(), 1.5)


if __name__ == "__main__":
    unittest.main()
