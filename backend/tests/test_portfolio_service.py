import sys
import unittest
from pathlib import Path

import pandas as pd

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.portfolio_service import (  # noqa: E402
    _portfolio_metrics,
    _validate_custom_weights,
    _normalize_weights,
)


class PortfolioServiceTest(unittest.TestCase):
    def test_portfolio_metrics_are_finite_for_normal_returns(self):
        returns = pd.Series([0.01, -0.005, 0.02, 0.0, -0.01, 0.015])
        metrics = _portfolio_metrics(returns)

        self.assertIsNotNone(metrics["totalReturn"])
        self.assertIsNotNone(metrics["annualReturn"])
        self.assertIsNotNone(metrics["annualVolatility"])
        self.assertIsNotNone(metrics["sharpeRatio"])
        self.assertLessEqual(metrics["maxDrawdown"], 0)
        self.assertGreaterEqual(metrics["positiveDays"], 0)
        self.assertLessEqual(metrics["positiveDays"], 1)

    def test_custom_weights_must_sum_to_100_percent(self):
        with self.assertRaises(ValueError):
            _validate_custom_weights(["AAPL", "MSFT"], {"AAPL": 60, "MSFT": 20})

    def test_custom_weights_reject_negative_values(self):
        with self.assertRaises(ValueError):
            _validate_custom_weights(["AAPL", "MSFT"], {"AAPL": 110, "MSFT": -10})

    def test_custom_weights_convert_percent_to_fractions(self):
        weights = _validate_custom_weights(["AAPL", "MSFT"], {"AAPL": 60, "MSFT": 40})

        self.assertAlmostEqual(weights["AAPL"], 0.6)
        self.assertAlmostEqual(weights["MSFT"], 0.4)

    def test_equal_weight_normalization(self):
        weights = _normalize_weights(["AAPL", "MSFT", "SPY"], None)

        self.assertAlmostEqual(sum(weights.values()), 1.0)
        self.assertAlmostEqual(weights["AAPL"], 1 / 3)


if __name__ == "__main__":
    unittest.main()
