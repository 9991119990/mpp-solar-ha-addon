import json
import re
import unittest
from pathlib import Path
from unittest import mock

from mpp_solar.mpp_solar_monitor import MPPSolarMonitor


ROOT = Path(__file__).resolve().parents[1]


class MetadataTests(unittest.TestCase):
    def test_release_version_is_2_0_10(self):
        config_yaml = (ROOT / "mpp_solar" / "config.yaml").read_text()
        yaml_version = re.search(r'^version:\s*"([^"]+)"', config_yaml, re.MULTILINE)

        self.assertIsNotNone(yaml_version)
        self.assertEqual("2.0.10", yaml_version.group(1))

    def test_config_json_is_valid_json(self):
        config_json = ROOT / "mpp_solar" / "config.json"
        json.loads(config_json.read_text())

    def test_versions_are_consistent(self):
        config_yaml = (ROOT / "mpp_solar" / "config.yaml").read_text()
        config_json = json.loads((ROOT / "mpp_solar" / "config.json").read_text())
        monitor_py = (ROOT / "mpp_solar" / "mpp_solar_monitor.py").read_text()

        yaml_version = re.search(r'^version:\s*"([^"]+)"', config_yaml, re.MULTILINE)
        sw_version = re.search(r'"sw_version":\s*"([^"]+)"', monitor_py)

        self.assertIsNotNone(yaml_version)
        self.assertIsNotNone(sw_version)
        self.assertEqual(yaml_version.group(1), config_json["version"])
        self.assertEqual(yaml_version.group(1), sw_version.group(1))

    def test_repository_yaml_uses_standard_maintainer_format(self):
        repository_yaml = (ROOT / "repository.yaml").read_text()
        maintainer = re.search(r'^maintainer:\s*"([^"]+)"', repository_yaml, re.MULTILINE)

        self.assertIsNotNone(maintainer)
        self.assertRegex(maintainer.group(1), r"^[^<>]+ <[^<>@\s]+@[^<>@\s]+>$")

    def test_dockerfile_includes_home_assistant_labels(self):
        dockerfile = (ROOT / "mpp_solar" / "Dockerfile").read_text()

        self.assertIn('io.hass.version="${BUILD_VERSION}"', dockerfile)
        self.assertIn('io.hass.type="app"', dockerfile)
        self.assertIn('io.hass.arch="${BUILD_ARCH}"', dockerfile)

    def test_dockerfile_sets_default_build_from_image(self):
        dockerfile = (ROOT / "mpp_solar" / "Dockerfile").read_text()
        build_from = re.search(r"^ARG BUILD_FROM=(.+)$", dockerfile, re.MULTILINE)

        self.assertIsNotNone(build_from)
        self.assertTrue(build_from.group(1).strip())

    def test_dockerfile_redeclares_build_args_after_from(self):
        dockerfile = (ROOT / "mpp_solar" / "Dockerfile").read_text()
        self.assertRegex(
            dockerfile,
            r"FROM \$BUILD_FROM\s+ARG BUILD_VERSION\s+ARG BUILD_ARCH",
        )


class MonitorTests(unittest.TestCase):
    @mock.patch("mpp_solar.mpp_solar_monitor.time.sleep", return_value=None)
    @mock.patch("mpp_solar.mpp_solar_monitor.os.access", return_value=False)
    @mock.patch("mpp_solar.mpp_solar_monitor.os.path.exists", return_value=True)
    def test_wait_for_device_returns_false_when_not_accessible(
        self, _exists, _access, _sleep
    ):
        monitor = MPPSolarMonitor()
        self.assertFalse(monitor.wait_for_device())


if __name__ == "__main__":
    unittest.main()
