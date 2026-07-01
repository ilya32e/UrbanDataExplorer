from __future__ import annotations

import sys
from pathlib import Path
import unittest

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "pipeline" / "src"
for path in (ROOT, SRC):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from urban_data_explorer.build import aggregate_sales_metrics, compute_quality_of_life_score, metric_catalog


class BuildMetricTests(unittest.TestCase):
    def test_aggregate_sales_metrics_keeps_detailed_sale_metrics(self) -> None:
        data = pd.DataFrame(
            [
                {
                    "arrondissement": 1,
                    "year": 2025,
                    "transaction_id": "a",
                    "price_per_m2": 10000,
                    "sale_value_eur": 200000,
                    "built_surface_m2": 20,
                    "rooms": 1,
                    "Type local": "Appartement",
                },
                {
                    "arrondissement": 1,
                    "year": 2025,
                    "transaction_id": "b",
                    "price_per_m2": 12000,
                    "sale_value_eur": 360000,
                    "built_surface_m2": 30,
                    "rooms": 2,
                    "Type local": "Maison",
                },
            ]
        )

        result = aggregate_sales_metrics(data, ["arrondissement", "year"]).iloc[0]

        self.assertEqual(result["transactions"], 2)
        self.assertEqual(result["median_price_m2"], 11000)
        self.assertEqual(result["median_sale_value_eur"], 280000)
        self.assertEqual(result["median_surface_m2"], 25)
        self.assertEqual(result["median_rooms"], 1.5)
        self.assertEqual(result["apartment_share_pct"], 50)
        self.assertEqual(result["house_share_pct"], 50)
        # Le seul appartement (1 piece) est un studio/T1, la maison n'entre dans aucune typologie T.
        self.assertEqual(result["studio_t1_share_pct"], 50)
        self.assertEqual(result["t2_share_pct"], 0)

    def test_aggregate_sales_metrics_splits_apartment_typologies(self) -> None:
        rooms_to_expected_column = {1: "studio_t1_share_pct", 2: "t2_share_pct", 3: "t3_share_pct", 4: "t4_share_pct", 6: "t5p_share_pct"}
        data = pd.DataFrame(
            [
                {
                    "arrondissement": 1,
                    "year": 2025,
                    "transaction_id": str(rooms),
                    "price_per_m2": 10000,
                    "sale_value_eur": 200000,
                    "built_surface_m2": 20,
                    "rooms": rooms,
                    "Type local": "Appartement",
                }
                for rooms in rooms_to_expected_column
            ]
        )

        result = aggregate_sales_metrics(data, ["arrondissement", "year"]).iloc[0]

        # Cinq appartements, un par typologie : chaque part vaut 20 %.
        for column in rooms_to_expected_column.values():
            self.assertEqual(result[column], 20)
        self.assertEqual(result["house_share_pct"], 0)

    def test_quality_of_life_score_bounds_extremes(self) -> None:
        summary = pd.DataFrame(
            [
                {
                    "noise_score": 1.0,
                    "air_score": 1.0,
                    "high_noise_share_pct": 0.0,
                    "environmental_pressure_index": 0.0,
                },
                {
                    "noise_score": 3.0,
                    "air_score": 3.0,
                    "high_noise_share_pct": 100.0,
                    "environmental_pressure_index": 100.0,
                },
            ]
        )

        scores = compute_quality_of_life_score(summary)

        self.assertEqual(scores.iloc[0], 10.0)
        self.assertEqual(scores.iloc[1], 0.0)

    def test_metric_catalog_exposes_environment_and_sales_metrics(self) -> None:
        metrics = metric_catalog()

        self.assertIn("median_sale_value_eur", metrics)
        self.assertIn("environmental_pressure_index", metrics)
        self.assertFalse(metrics["social_units_financed"]["supports_year"])


if __name__ == "__main__":
    unittest.main()
