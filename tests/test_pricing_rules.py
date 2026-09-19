import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.manage_db import build_site, compute_price_guide, connect, display_rows, ingest_payload, migrate

KST = timezone(timedelta(hours=9))


class PricingRulesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.connection = connect(Path(self.temp.name) / "test.sqlite")
        migrate(self.connection)
        self.as_of = datetime(2026, 9, 20, 12, 0, tzinfo=KST)

    def tearDown(self):
        self.connection.close()
        self.temp.cleanup()

    def listing(self, listing_id, price, age_days, seller, *, model="Test Camera", state="active", sold_age_days=None):
        stamp = self.as_of - timedelta(days=age_days)
        return {
            "marketplace": "joongna", "external_listing_id": listing_id,
            "brand": "Test", "model": model, "variant": "Body",
            "seller_external_id": seller, "seller_name": seller,
            "title": f"{model} {listing_id}",
            "listing_url": f"https://web.joongna.com/product/{listing_id}",
            "price_krw": price, "state": state,
            "listed_at": stamp.isoformat(), "updated_at": stamp.isoformat(),
            "sold_at": ((self.as_of - timedelta(days=sold_age_days)).isoformat() if sold_age_days is not None else None),
            "is_comparable": True,
        }

    def safety(self, seller, count):
        return {
            "marketplace": "joongna", "seller_external_id": seller,
            "checked_at": self.as_of.isoformat(), "verification_status": "verified",
            "safe_trade_count": count,
            "source_url": f"https://web.joongna.com/user/{seller}",
        }

    def test_25_day_cutoff_and_safe_column(self):
        payload = {
            "run_id": "fixture", "fetched_at": self.as_of.isoformat(),
            "listings": [
                self.listing("old-cheap", 50, 26, "safe-seller"),
                self.listing("zero-low", 100, 2, "zero-seller"),
                self.listing("safe-low", 120, 2, "safe-seller"),
                self.listing("sold-10", 80, 10, "safe-seller", state="sold", sold_age_days=10),
                self.listing("sold-100", 70, 100, "safe-seller", state="sold", sold_age_days=100),
                self.listing("sold-190", 60, 190, "safe-seller", state="sold", sold_age_days=190),
            ],
            "seller_safety_checks": [self.safety("zero-seller", 0), self.safety("safe-seller", 2)],
        }
        ingest_payload(self.connection, payload)
        run_id = compute_price_guide(self.connection, self.as_of.isoformat(), "test-25-day")
        row = display_rows(self.connection, run_id)[0]
        self.assertEqual(row["current"], 100)
        self.assertEqual(row["currentUrl"], "https://web.joongna.com/product/zero-low")
        self.assertEqual(row["safe"], 120)
        self.assertEqual(row["safeUrl"], "https://web.joongna.com/product/safe-low")
        self.assertEqual(row["safety"], "주의 · 안전거래 0회")
        self.assertEqual(row["low6"], 70)
        self.assertEqual(row["avg3"], 80)
        self.assertEqual(row["n3"], 1)
        with tempfile.TemporaryDirectory() as output:
            build_site(self.connection, Path(output))
            html = (Path(output) / "index.html").read_text()
            self.assertIn("판매중은 최근 25일 이내만", html)
            self.assertIn("안전거래 0회 또는 이력 확인 불가 판매자", html)
            self.assertIn("가격 매력도", html)
            self.assertIn("function deal(x)", html)

    def test_unavailable_history_is_caution_but_safe_listing_remains(self):
        payload = {
            "run_id": "fixture-2", "fetched_at": self.as_of.isoformat(),
            "listings": [
                self.listing("unknown-low", 90, 1, None, model="Test Phone"),
                self.listing("verified-safe", 110, 1, "safe-seller", model="Test Phone"),
            ],
            "seller_safety_checks": [self.safety("safe-seller", 1)],
        }
        ingest_payload(self.connection, payload)
        run_id = compute_price_guide(self.connection, self.as_of.isoformat(), "test-unavailable")
        row = next(row for row in display_rows(self.connection, run_id) if row["model"] == "Test Phone")
        self.assertEqual(row["current"], 90)
        self.assertEqual(row["safety"], "주의 · 안전거래 이력 확인불가")
        self.assertEqual(row["safe"], 110)
        self.assertEqual(row["safeUrl"], "https://web.joongna.com/product/verified-safe")

    def test_exactly_25_days_is_included(self):
        exact = self.listing("exact-25", 100, 25, "safe-seller", model="Boundary")
        too_old = self.listing("older-than-25", 50, 25, "safe-seller", model="Boundary")
        too_old["listed_at"] = (self.as_of - timedelta(days=25, seconds=1)).isoformat()
        too_old["updated_at"] = too_old["listed_at"]
        ingest_payload(
            self.connection,
            {
                "run_id": "fixture-boundary",
                "fetched_at": self.as_of.isoformat(),
                "listings": [exact, too_old],
                "seller_safety_checks": [self.safety("safe-seller", 1)],
            },
        )
        run_id = compute_price_guide(
            self.connection, self.as_of.isoformat(), "test-boundary"
        )
        row = next(row for row in display_rows(self.connection, run_id) if row["model"] == "Boundary")
        self.assertEqual(row["current"], 100)
        self.assertEqual(row["safe"], 100)


if __name__ == "__main__":
    unittest.main()
