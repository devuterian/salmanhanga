import unittest

from scripts.manage_joongna_alerts import keyword_payload


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


if __name__ == "__main__":
    unittest.main()
