import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from services.learning_service import list_lessons  # noqa: E402
from services.research_service import list_research_portfolios  # noqa: E402
from services.simulation_service import get_simulation_templates  # noqa: E402
from services.translation_service import detect_language, translate_texts  # noqa: E402
from services.yfinance_service import search_symbols  # noqa: E402


class TranslationAndLearningTest(unittest.TestCase):
    def test_detect_language_handles_chinese_english_and_japanese(self):
        self.assertEqual(detect_language("什么是 ETF"), "zh-CN")
        self.assertEqual(detect_language("What is a bond yield?"), "en")
        self.assertEqual(detect_language("日銀と物価"), "ja")

    def test_translate_texts_without_api_key_keeps_original_text(self):
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}, clear=False):
            response = translate_texts(["What is inflation?"])

        self.assertTrue(response["success"])
        self.assertFalse(response["data"]["available"])
        self.assertEqual(response["data"]["translations"], ["What is inflation?"])
        self.assertIn("DEEPSEEK_API_KEY", response["meta"]["warnings"][0])

    def test_learning_service_includes_domestic_public_sources(self):
        response = list_lessons()

        self.assertTrue(response["success"])
        lessons = response["data"]["lessons"]
        source_names = {item["sourceName"] for item in lessons}
        self.assertIn("中国投资者网", source_names)
        self.assertIn("上交所投资者教育", source_names)
        self.assertTrue(any(item["language"] == "zh-CN" for item in lessons))

    def test_search_supports_chinese_aliases_and_featured_assets(self):
        apple = search_symbols("苹果", 5)
        self.assertEqual(apple[0]["symbol"], "AAPL")
        self.assertIn("苹果", apple[0]["aliases"])
        featured = search_symbols("", 5)
        self.assertEqual(len(featured), 5)
        self.assertTrue(all(item["isPopular"] for item in featured))

    def test_simulation_and_research_catalogs_are_expanded(self):
        self.assertGreaterEqual(len(get_simulation_templates()), 4)
        self.assertGreaterEqual(len(list_research_portfolios()["data"]["portfolios"]), 13)


if __name__ == "__main__":
    unittest.main()
