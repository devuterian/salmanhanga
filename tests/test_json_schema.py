import unittest

from scripts.validate_json import ROOT, validate


class JsonSchemaTest(unittest.TestCase):
    def test_listing_import_contract_and_external_safety_ref(self):
        payload = validate(
            ROOT / "tests" / "fixtures" / "listing-import.valid.json",
            "listing-import.schema.json",
        )
        self.assertEqual(payload["seller_safety_checks"][0]["safe_trade_count"], 0)


if __name__ == "__main__":
    unittest.main()
