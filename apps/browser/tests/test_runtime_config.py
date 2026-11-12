import importlib.util
from pathlib import Path
import unittest

RUNNER=Path(__file__).resolve().parents[1]/"runner.py"
spec=importlib.util.spec_from_file_location("runner_config",RUNNER)
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)

class RuntimeConfigTests(unittest.TestCase):
    def test_chromium_sandbox_defaults_to_enabled(self):
        self.assertTrue(runner.chromium_sandbox_enabled(None))
        self.assertTrue(runner.chromium_sandbox_enabled("true"))
    def test_chromium_sandbox_can_be_disabled_for_restricted_container_runtime(self):
        self.assertFalse(runner.chromium_sandbox_enabled("false"))
        self.assertFalse(runner.chromium_sandbox_enabled("0"))
