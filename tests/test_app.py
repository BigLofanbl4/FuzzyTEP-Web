import unittest

from app import analyse_indicators, normalize_enterprise_payload


class AnalyseIndicatorsTests(unittest.TestCase):
    def test_high_efficiency_case(self):
        result = analyse_indicators(
            {
                "period": "2026-03",
                "revenue": 10000000,
                "profit": 2600000,
                "revenue_growth": 18,
                "liquidity_ratio": 1.85,
            },
            enterprise={"industry": "Машиностроение"},
        )
        self.assertEqual(result["industry_profile"], "manufacturing")
        self.assertEqual(result["efficiency_label"], "высокая")
        self.assertGreaterEqual(result["numeric_score"], 80)
        self.assertGreaterEqual(len(result["triggered_rules"]), 3)
        self.assertAlmostEqual(result["costs"], 7400000)
        self.assertTrue(result["main_takeaway"])
        self.assertTrue(result["strengths"])
        self.assertTrue(result["actions"])
        self.assertIn("meaning", result["triggered_rules"][0])
        self.assertIn("action_hint", result["triggered_rules"][0])

    def test_low_efficiency_case(self):
        result = analyse_indicators(
            {
                "period": "2026-03",
                "revenue": 6000000,
                "profit": 120000,
                "revenue_growth": -8,
                "liquidity_ratio": 0.82,
            },
            enterprise={"industry": "Торговля"},
        )
        self.assertEqual(result["efficiency_label"], "низкая")
        self.assertEqual(result["industry_profile"], "trade")
        self.assertLess(result["numeric_score"], 35)
        self.assertTrue(result["risks"])
        self.assertIn("слабой устойчивости", result["main_takeaway"])

    def test_mid_efficiency_case(self):
        result = analyse_indicators(
            {
                "period": "2026-03",
                "revenue": 7500000,
                "profit": 900000,
                "revenue_growth": 6,
                "liquidity_ratio": 1.18,
            },
            enterprise={"industry": "Услуги"},
        )
        self.assertIn(result["efficiency_label"], {"удовлетворительная", "хорошая"})
        self.assertGreater(result["numeric_score"], 35)
        self.assertLess(result["numeric_score"], 80)
        self.assertTrue(result["comment"])
        self.assertTrue(result["explanation"])

    def test_explicit_profile_is_used_for_analysis(self):
        result = analyse_indicators(
            {
                "period": "2026-03",
                "revenue": 5000000,
                "profit": 700000,
                "revenue_growth": 7,
                "liquidity_ratio": 1.3,
            },
            enterprise={"industry": "Неизвестная отрасль", "profile_code": "services"},
        )
        self.assertEqual(result["industry_profile"], "services")

    def test_enterprise_payload_can_be_saved_without_industry_field(self):
        payload = normalize_enterprise_payload(
            {
                "name": "Тест",
                "profile_code": "trade",
                "ownership": "ООО",
                "description": "Описание",
            }
        )
        self.assertEqual(payload["profile_code"], "trade")
        self.assertEqual(payload["industry"], "торговля")

    def test_zero_revenue_is_rejected(self):
        with self.assertRaises(ValueError):
            analyse_indicators(
                {
                    "period": "2026-03",
                    "revenue": 0,
                    "profit": 10,
                    "revenue_growth": 0,
                    "liquidity_ratio": 1.2,
                }
            )

    def test_profit_must_be_less_than_revenue(self):
        with self.assertRaises(ValueError):
            analyse_indicators(
                {
                    "period": "2026-03",
                    "revenue": 1000,
                    "profit": 1000,
                    "revenue_growth": 5,
                    "liquidity_ratio": 1.2,
                }
            )


if __name__ == "__main__":
    unittest.main()
