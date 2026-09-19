import unittest

from scripts.normalize_mcp_refresh import capacity, choose_variant, comparable, model_matches


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

    def test_separates_new_nearby_models(self):
        cases = [
            ("iPhone 14 Pro", "아이폰 14 프로맥스 256GB"),
            ("Ricoh GR IV", "리코 GR III HDF 카메라"),
            ("Ricoh GR IV", "리코 GR IV HDF 카메라"),
            ("GoPro MISSION 1", "고프로 Mission 1 Pro"),
            ("MacBook Pro M4 Pro", "맥북프로 16 M4 Max"),
        ]
        for model, title in cases:
            with self.subTest(model=model, title=title):
                self.assertFalse(model_matches(model, title))

    def test_assigns_new_variants(self):
        self.assertEqual(
            choose_variant("DJI Mini 5 Pro", ["스탠다드", "플라이 모어"], "DJI 미니5 프로 플라이 모어 콤보"),
            "플라이 모어",
        )
        self.assertEqual(
            choose_variant("MacBook Air M4", ["13인치", "15인치"], "맥북에어 M4 15인치"),
            "15인치",
        )
        self.assertEqual(
            choose_variant(
                "Apple Watch Series 10",
                ["42mm GPS", "42mm Cellular", "46mm GPS", "46mm Cellular"],
                "애플워치10 46mm 셀룰러",
            ),
            "46mm Cellular",
        )

    def test_rtx_laptop_stays_excluded(self):
        product = {"brand": "NVIDIA", "model": "RTX 4080", "variant": "16GB"}
        self.assertFalse(comparable(product, "RTX 4080 노트북", None, 2_000_000))

    def test_single_capacity_and_no_burn_in_wording(self):
        self.assertEqual(choose_variant("Galaxy S22", ["256GB"], "갤럭시 S22 무잔상"), "256GB")
        product = {"brand": "Samsung", "model": "Galaxy S22", "variant": "256GB"}
        self.assertTrue(comparable(product, "갤럭시 S22 256GB 무잔상", None, 280_000))

    def test_terabyte_capacity_before_korean_text(self):
        self.assertEqual(capacity("갤럭시 S23 울트라 1TB 그린"), "1TB")
        self.assertEqual(capacity("갤럭시 S23 울트라 1테라 S급"), "1TB")


if __name__ == "__main__":
    unittest.main()
