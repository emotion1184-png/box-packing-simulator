"""데이터 저장소 (Excel 기반)."""

import streamlit as st
from typing import List
from pathlib import Path

from core.excel_loader import CatalogLoadResult, load_catalog
from core.models import PackBox, ProductBox


class DataStorage:
    """Excel 기반 데이터 저장소"""

    def __init__(self):
        if "pack_boxes" not in st.session_state or "product_boxes" not in st.session_state:
            self._load_from_excel()

    def _load_from_excel(self):
        """엑셀에서 데이터 로딩"""

        excel_path = Path(__file__).resolve().parents[2] / "data" / "box_data.xlsx"

        if not excel_path.exists():
            st.error("data/box_data.xlsx 파일이 없습니다.")
            st.stop()

        try:
            catalog = load_catalog(excel_path)
        except Exception as e:
            st.error(f"엑셀 로딩 오류: {e}")
            st.stop()

        if catalog.pack_boxes is None:
            st.error("기본 데이터에 'pack_boxes' 시트가 없습니다.")
            st.stop()

        self.apply_catalog(catalog)

    def get_pack_boxes(self) -> List[PackBox]:
        return st.session_state.pack_boxes

    def get_product_boxes(self) -> List[ProductBox]:
        return st.session_state.product_boxes

    def add_pack_box(self, box: PackBox):
        existing = [b for b in st.session_state.pack_boxes if b.name == box.name]
        if existing:
            st.session_state.pack_boxes = [
                b for b in st.session_state.pack_boxes if b.name != box.name
            ]
        st.session_state.pack_boxes.append(box)

    def add_product_box(self, prod: ProductBox):
        existing = [
            p
            for p in st.session_state.product_boxes
            if p.product_id == prod.product_id
        ]
        if existing:
            st.session_state.product_boxes = [
                p
                for p in st.session_state.product_boxes
                if p.product_id != prod.product_id
            ]
        st.session_state.product_boxes.append(prod)

    def replace_pack_boxes(self, boxes: List[PackBox]):
        st.session_state.pack_boxes = list(boxes)

    def replace_product_boxes(self, products: List[ProductBox]):
        st.session_state.product_boxes = list(products)

    def apply_catalog(self, catalog: CatalogLoadResult):
        if catalog.pack_boxes is not None:
            self.replace_pack_boxes(catalog.pack_boxes)
        self.replace_product_boxes(catalog.product_boxes)
        st.session_state.catalog_status = {
            "product_sheet": catalog.product_sheet,
            "skipped_product_rows": catalog.skipped_product_rows,
        }

    def delete_pack_box(self, name: str):
        st.session_state.pack_boxes = [
            b for b in st.session_state.pack_boxes if b.name != name
        ]

    def delete_product_box(self, product_id: str):
        st.session_state.product_boxes = [
            p
            for p in st.session_state.product_boxes
            if p.product_id != product_id
        ]
