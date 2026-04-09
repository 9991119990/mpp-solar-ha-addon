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

        self.assertLessEqual(monitor.get_read_deadline_seconds(), 2.0)

    def test_response_is_incomplete_without_closing_frame_and_crc(self):
        monitor = MPPSolarMonitor()

        self.assertFalse(monitor.has_complete_response_frame(b"(230.0 50.0 230.0\r"))

    def test_response_is_complete_with_payload_crc_and_carriage_return(self):
        monitor = MPPSolarMonitor()

        self.assertTrue(monitor.has_complete_response_frame(b"(230.0 50.0 230.0)AB\r"))

    def test_extract_complete_frame_returns_frame_and_remaining_bytes(self):
        monitor = MPPSolarMonitor()

        frame, remaining = monitor.extract_complete_response_frame(
            b"junk(230.0 50.0 230.0)AB\rtail"
        )

        self.assertEqual(frame, b"(230.0 50.0 230.0)AB\r")
        self.assertEqual(remaining, b"tail")

    def test_extract_complete_frame_keeps_partial_tail_for_next_cycle(self):
        monitor = MPPSolarMonitor()

        frame, remaining = monitor.extract_complete_response_frame(
            b"noise(230.0 50.0 230.0)AB\r(48.0 10"
        )

        self.assertEqual(frame, b"(230.0 50.0 230.0)AB\r")
        self.assertEqual(remaining, b"(48.0 10")

    def test_extract_values_from_partial_response_without_closing_frame(self):
        monitor = MPPSolarMonitor()

        values = monitor.extract_values_from_response(
            b"(230.0 50.0 230.0 50.0 2500 2343 046 420 52.00 27 048 0033 05.0 105.7 54.00 000 00010000"
        )

        self.assertIsNotNone(values)
        self.assertGreaterEqual(len(values), 17)
        self.assertEqual(values[5], "2343")

    def test_extract_values_from_response_ignores_noise_before_frame(self):
        monitor = MPPSolarMonitor()

        values = monitor.extract_values_from_response(
            b"junkjunk(230.0 50.0 230.0 50.0 2500 2343 046 420 52.00 27 048 0033 05.0 105.7 54.00 000 00010000"
        )

        self.assertIsNotNone(values)
        self.assertEqual(values[0], "230.0")


if __name__ == "__main__":
    unittest.main()
