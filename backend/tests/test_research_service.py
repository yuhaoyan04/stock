import sys
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.research_service import (  # noqa: E402
    DISCLOSURE_WARNING,
    get_research_portfolio,
    list_research_portfolios,
)


class ResearchServiceTest(unittest.TestCase):
    def test_list_research_portfolios_returns_templates(self):
        response = list_research_portfolios()

        self.assertTrue(response["success"])
        portfolios = response["data"]["portfolios"]
        self.assertGreaterEqual(len(portfolios), 9)
        self.assertIn("disclosureDate", portfolios[0])
        self.assertIn(DISCLOSURE_WARNING, response["meta"]["warnings"])

    def test_get_research_portfolio_normalizes_weights(self):
        response = get_research_portfolio("berkshire")

        self.assertTrue(response["success"])
        data = response["data"]
        self.assertAlmostEqual(sum(item["weight"] for item in data["holdings"]), 1.0, places=5)
        self.assertEqual(data["id"], "berkshire")
        self.assertIn(DISCLOSURE_WARNING, data["warnings"])

    def test_unknown_research_portfolio_raises_value_error(self):
        with self.assertRaises(ValueError):
            get_research_portfolio("missing")


if __name__ == "__main__":
    unittest.main()
