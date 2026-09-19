import unittest

from scripts.normalize_mcp_refresh import model_matches


class ModelMatchTest(unittest.TestCase):
    def test_rejects_nearby_models(self):
        cases = [
            ("iPhone 16", "아이폰 16pro 256GB"),
            ("iPhone 17", "아이폰 17e 256GB"),
            ("Canon R1", "캐논 R10 바디"),
            ("Nikon Zf", "니콘 Zfc 바디"),
            ("Sony FX3", "소니 FX30 바디"),
            ("Fujifilm X-E5", "후지 X-E4 바디, X-E5 문의"),
            ("Fujifilm X100VI", "후지 X100V, X100VI 문의"),
        ]
        for model, title in cases:
            with self.subTest(model=model, title=title):
                self.assertFalse(model_matches(model, title))

    def test_accepts_exact_models(self):
        self.assertTrue(model_matches("iPhone 16 Pro", "아이폰16 프로 256GB"))
        self.assertTrue(model_matches("Canon R10", "캐논 R10 바디"))
        self.assertTrue(model_matches("Sony a7 III", "소니 A7M3 바디"))


if __name__ == "__main__":
    unittest.main()
