"""Тесты verbose-диагностики двуязычности."""
import os
import unittest

from tests.helpers import ROOT, run_main_cli


class TestBilingualVerbose(unittest.TestCase):
    def test_verbose_logs_bilingual_token_labels(self):
        alg = os.path.join(ROOT, "examples", "en", "01_hello.alg")
        result = run_main_cli([alg, "--verbose"], timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("алг / proc", result.stderr)
        self.assertIn("нач / begin", result.stderr)
        self.assertIn("[токен]", result.stderr)


if __name__ == "__main__":
    unittest.main()
