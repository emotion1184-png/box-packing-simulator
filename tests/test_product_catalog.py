import sys
import unittest
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "app"))

from core.excel_loader import products_from_list_dataframe
from core.models import PackBox, PaddingConfig
from core.packing import run_packing_simulation
from core.product_catalog import filter_products, product_label


class ProductCatalogTests(unittest.TestCase):
    def setUp(self):
        dataframe = pd.DataFrame(
            [
                {
                    "대분류": "LED조명등",
                    "시리즈": "QCML",
                    "모델": "QCML-1200",
                    "sku": "Y-SHARED",
                    "name": "제품박스 A",
                    "l": 10,
                    "w": 20,
                    "h": 30,
                    "weight": 0.5,
                    "rotatable": True,
                    "note": None,
                },
                {
                    "대분류": "LED조명등",
                    "시리즈": "QCML",
                    "모델": "QCML-1500",
                    "sku": "Y-SHARED",
                    "name": "제품박스 A",
                    "l": 10,
                    "w": 20,
                    "h": 30,
                    "weight": 0.6,
                    "rotatable": True,
                    "note": None,
                },
                {
                    "대분류": "리미트스위치",
                    "시리즈": "SLP2130",
                    "모델": "SLP2130",
                    "sku": "Y-MISSING",
                    "name": None,
                    "l": None,
                    "w": None,
                    "h": None,
                    "weight": None,
                    "rotatable": True,
                    "note": None,
                },
            ]
        )
        self.products, self.skipped = products_from_list_dataframe(dataframe)

    def test_list_rows_are_distinct_by_model_even_when_sku_matches(self):
        self.assertEqual(2, len(self.products))
        self.assertEqual(1, self.skipped)
        self.assertEqual(
            {"QCML-1200", "QCML-1500"},
            {product.product_id for product in self.products},
        )

    def test_search_and_label_put_model_first(self):
        matched = filter_products(self.products, ["1500"])
        self.assertEqual(["QCML-1500"], [product.model for product in matched])
        self.assertTrue(product_label(matched[0]).startswith("QCML-1500 |"))

    def test_packing_keeps_models_separate(self):
        pack_box = PackBox(
            name="테스트 박스",
            inner_L=100,
            inner_W=100,
            inner_H=100,
            outer_L=105,
            outer_W=105,
            outer_H=105,
        )
        result = run_packing_simulation(
            pack_box,
            [(self.products[0], 1), (self.products[1], 1)],
            PaddingConfig(),
            num_trials=5,
        )
        self.assertEqual(
            {"QCML-1200", "QCML-1500"},
            {item.product_id for item in result.fitted_items},
        )


if __name__ == "__main__":
    unittest.main()
