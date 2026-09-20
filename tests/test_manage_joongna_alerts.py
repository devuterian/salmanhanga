import unittest

from scripts.manage_joongna_alerts import DEFAULT_MIN_PRICE, alerts_by_keyword, keyword_payload


class JoongnaAlertTest(unittest.TestCase):
    def test_keyword_payload_keeps_price_range_and_safe_defaults(self):
        payload = keyword_payload("  Galaxy S23 Ultra  ", min_price=300000, max_price=650000)

        self.assertEqual(payload["tagKeywordName"], "Galaxy S23 Ultra")
        self.assertEqual(payload["productStartPrice"], 300000)
        self.assertEqual(payload["productEndPrice"], 650000)
        self.assertEqual(payload["productCondition"], 3)
        self.assertEqual(payload["productColor"], "ZZZZZZ")
        self.assertEqual(payload["keywordLocation"], [])
        self.assertTrue(payload["isKeywordDuplicateCheck"])

    def test_update_payload_includes_keyword_sequence(self):
        payload = keyword_payload(
            "S23 Ultra", min_price=None, max_price=600000, user_keyword_seq=1234
        )

        self.assertEqual(payload["userKeywordSeq"], 1234)
        self.assertEqual(payload["productStartPrice"], DEFAULT_MIN_PRICE)

    def test_rejects_price_below_default_floor(self):
        with self.assertRaisesRegex(ValueError, "100,000원 이상"):
            keyword_payload("S23 Ultra", min_price=0, max_price=600000)

    def test_rejects_max_price_below_min_price(self):
        with self.assertRaisesRegex(ValueError, "최저 가격보다 낮을 수 없습니다"):
            keyword_payload("S23 Ultra", min_price=200000, max_price=100000)

    def test_alert_lookup_ignores_api_keyword_case_normalization(self):
        alerts = alerts_by_keyword([{"tagKeywordName": "갤럭시 S24 울트라"}])
        self.assertIn("갤럭시 s24 울트라", alerts)


if __name__ == "__main__":
    unittest.main()
