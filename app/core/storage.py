"""
데이터 저장소 (Excel 기반)
"""
import streamlit as st
import pandas as pd
from typing import List
from pathlib import Path

from core.models import PackBox, ProductBox


class DataStorage:
    """Excel 기반 데이터 저장소"""

    def __init__(self):
        if "pack_boxes" not in st.session_state or "product_boxes" not in st.session_state:
            self._load_from_excel()

    def _load_from_excel(self):
        """엑셀에서 데이터 로딩"""

        excel_path = Path("data/box_data.xlsx")

        if not excel_path.exists():
            st.error("data/box_data.xlsx 파일이 없습니다.")
            st.stop()

        try:
            pack_df = pd.read_excel(excel_path, sheet_name="pack_boxes")
            prod_df = pd.read_excel(excel_path, sheet_name="product_boxes")
        except Exception as e:
            st.error(f"엑셀 로딩 오류: {e}")
            st.stop()

        pack_boxes: List[PackBox] = []
        product_boxes: List[ProductBox] = []

        for _, row in pack_df.iterrows():
            pack_boxes.append(
                PackBox(
                    name=str(row["name"]),
                    inner_L=float(row["inner_L"]),
                    inner_W=float(row["inner_W"]),
                    inner_H=float(row["inner_H"]),
                    outer_L=float(row["outer_L"]),
                    outer_W=float(row["outer_W"]),
                    outer_H=float(row["outer_H"]),
                    max_weight=float(row["max_weight"]) if not pd.isna(row["max_weight"]) else None,
                    note=str(row["note"]) if not pd.isna(row["note"]) else "",
                )
            )

        for _, row in prod_df.iterrows():
            product_boxes.append(
                ProductBox(
                    sku=str(row["sku"]),
                    name=str(row["name"]),
                    l=float(row["L"]),
                    w=float(row["W"]),
                    h=float(row["H"]),
                    weight=float(row["weight"]) if not pd.isna(row["weight"]) else 0,
                    rotatable=bool(row["rotatable"]),
                    note=str(row["note"]) if not pd.isna(row["note"]) else "",
                )
            )

        st.session_state.pack_boxes = pack_boxes
        st.session_state.product_boxes = product_boxes

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
        existing = [p for p in st.session_state.product_boxes if p.sku == prod.sku]
        if existing:
            st.session_state.product_boxes = [
                p for p in st.session_state.product_boxes if p.sku != prod.sku
            ]
        st.session_state.product_boxes.append(prod)

    def delete_pack_box(self, name: str):
        st.session_state.pack_boxes = [
            b for b in st.session_state.pack_boxes if b.name != name
        ]

    def delete_product_box(self, sku: str):
        st.session_state.product_boxes = [
            p for p in st.session_state.product_boxes if p.sku != sku
        ]
