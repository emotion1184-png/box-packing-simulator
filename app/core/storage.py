# app/core/storage.py
"""
데이터 저장소 (Session State 기반 + 샘플 데이터)
"""
import streamlit as st
from typing import List
from core.models import PackBox, ProductBox

class DataStorage:
    """세션 기반 데이터 저장소"""
    
    def __init__(self):
        if 'pack_boxes' not in st.session_state:
            st.session_state.pack_boxes = self._get_sample_pack_boxes()
        if 'product_boxes' not in st.session_state:
            st.session_state.product_boxes = self._get_sample_product_boxes()
    
    def _get_sample_pack_boxes(self) -> List[PackBox]:
        """샘플 포장박스"""
        return [
            PackBox(
                name="박스X",
                inner_L=595, inner_W=380, inner_H=420,
                outer_L=600, outer_W=385, outer_H=425,
                max_weight=30, note="중형 포장박스"
            ),
            PackBox(
                name="박스Y",
                inner_L=490, inner_W=310, inner_H=350,
                outer_L=495, outer_W=315, outer_H=355,
                max_weight=20, note="소형 포장박스"
            ),
            PackBox(
                name="박스Z",
                inner_L=700, inner_W=450, inner_H=500,
                outer_L=705, outer_W=455, outer_H=505,
                max_weight=50, note="대형 포장박스"
            ),
        ]
    
    def _get_sample_product_boxes(self) -> List[ProductBox]:
        """샘플 제품박스"""
        return [
            ProductBox(
                sku="K001",
                name="제품K",
                l=560, w=280, h=200,
                weight=5, rotatable=True, note="표준 제품"
            ),
            ProductBox(
                sku="M001",
                name="제품M",
                l=300, w=200, h=150,
                weight=3, rotatable=True, note="소형 제품"
            ),
            ProductBox(
                sku="N001",
                name="제품N",
                l=400, w=250, h=180,
                weight=4, rotatable=False, note="회전금지 제품"
            ),
        ]
    
    def get_pack_boxes(self) -> List[PackBox]:
        return st.session_state.pack_boxes
    
    def get_product_boxes(self) -> List[ProductBox]:
        return st.session_state.product_boxes
    
    def add_pack_box(self, box: PackBox):
        # 중복 체크
        existing = [b for b in st.session_state.pack_boxes if b.name == box.name]
        if existing:
            # 덮어쓰기
            st.session_state.pack_boxes = [b for b in st.session_state.pack_boxes if b.name != box.name]
        st.session_state.pack_boxes.append(box)
    
    def add_product_box(self, prod: ProductBox):
        existing = [p for p in st.session_state.product_boxes if p.sku == prod.sku]
        if existing:
            st.session_state.product_boxes = [p for p in st.session_state.product_boxes if p.sku != prod.sku]
        st.session_state.product_boxes.append(prod)
    
    def delete_pack_box(self, name: str):
        st.session_state.pack_boxes = [b for b in st.session_state.pack_boxes if b.name != name]
    
    def delete_product_box(self, sku: str):
        st.session_state.product_boxes = [p for p in st.session_state.product_boxes if p.sku != sku]
