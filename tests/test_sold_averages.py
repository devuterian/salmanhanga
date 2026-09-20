import unittest

from scripts.refresh_sold_averages import alert_max_price, comparable_prices


class SoldAverageTest(unittest.TestCase):
    def test_alert_price_is_15_percent_below_and_rounded_down(self):
        self.assertEqual(alert_max_price(580_850), 490_000)
        self.assertLessEqual(alert_max_price(580_850), 580_850 * 0.85)

    def test_comparable_prices_remove_floor_and_large_outlier(self):
        self.assertEqual(
            comparable_prices([50_000, 400_000, 500_000, 600_000, 2_000_000], 100_000),
            [400_000, 500_000, 600_000],
        )


if __name__ == "__main__":
    unittest.main()
