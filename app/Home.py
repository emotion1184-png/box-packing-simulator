# app/Home.py
"""
박스 적치 시뮬레이션 - 홈 페이지
"""
import streamlit as st
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))

# 페이지 설정
st.set_page_config(
    page_title="Box Packing Simulator",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 로드
def load_css():
    st.markdown("""
    <style>
    /* 메인 헤더 */
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin: 2rem 0;
    }
    
    /* 카드 스타일 */
    .feature-card {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.07);
        border: 1px solid #e0e0e0;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 100%;
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        font-size: 3rem;
        margin-bottom: 1rem;
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #333;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        color: #666;
        line-height: 1.6;
    }
    
    /* 액션 버튼 */
    .action-btn {
        display: inline-block;
        padding: 0.8rem 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 25px;
        text-decoration: none;
        font-weight: 600;
        transition: transform 0.3s ease;
    }
    
    .action-btn:hover {
        transform: scale(1.05);
    }
    
    /* 통계 카드 */
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        font-size: 1rem;
        opacity: 0.9;
    }
    
    /* 사이드바 커스터마이징 */
    section[data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    
    /* 메트릭 스타일 */
    .stMetric {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }
    </style>
    """, unsafe_allow_html=True)

load_css()

# 타이틀
st.markdown('<div class="main-header">📦 Box Packing Simulator</div>', unsafe_allow_html=True)

# 서브타이틀
st.markdown("""
<div style="text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 3rem;">
Smart packaging solution with 3D visualization
</div>
""", unsafe_allow_html=True)

# 기능 카드
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">📊</div>
        <div class="feature-title">Pack Simulator</div>
        <div class="feature-desc">
        Calculate maximum packing capacity for selected box with multiple products
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🏆</div>
        <div class="feature-title">Box Recommender</div>
        <div class="feature-desc">
        Find the most efficient packaging box for your product combination
        </div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div class="feature-icon">🎨</div>
        <div class="feature-title">3D Visualization</div>
        <div class="feature-desc">
        Interactive 3D view with detailed packing layout and coordinates
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 빠른 시작 가이드
st.markdown("### 🚀 Quick Start")
st.markdown("""
1. **Upload Data** - Import the Excel `리스트` sheet (the `타워` sheet is ignored)
2. **Pack Simulator** - Select a packaging box and products to simulate packing
3. **Box Recommender** - Find the best box for your product combination
4. **Export Results** - Download CSV or HTML with 3D visualization
""")

# 사이드바 - 데이터 관리
from core.storage import DataStorage
from core.excel_loader import load_catalog
import pandas as pd
import io

st.sidebar.title("📦 Data Management")

storage = DataStorage()

# 엑셀 업로드
uploaded_file = st.sidebar.file_uploader("📥 Upload Excel", type=['xlsx', 'xls'])
if uploaded_file:
    try:
        catalog = load_catalog(uploaded_file)
        storage.apply_catalog(catalog)

        skipped_message = (
            f" / skipped {catalog.skipped_product_rows} invalid row(s)"
            if catalog.skipped_product_rows
            else ""
        )
        st.sidebar.success(
            f"✅ Loaded '{catalog.product_sheet}': "
            f"{len(catalog.product_boxes)} models{skipped_message}"
        )
        if catalog.product_sheet == "리스트":
            st.sidebar.caption("Only the '리스트' sheet was imported. '타워' was ignored.")
    except Exception as e:
        st.sidebar.error(f"❌ Upload error: {e}")

# 엑셀 다운로드
if st.sidebar.button("📤 Download Current Data"):
    pack_boxes = storage.get_pack_boxes()
    product_boxes = storage.get_product_boxes()
    
    pack_data = []
    for box in pack_boxes:
        pack_data.append({
            'name': box.name,
            'inner_L': box.inner_L,
            'inner_W': box.inner_W,
            'inner_H': box.inner_H,
            'outer_L': box.outer_L,
            'outer_W': box.outer_W,
            'outer_H': box.outer_H,
            'max_weight': box.max_weight or 0,
            'note': box.note or ''
        })
    
    list_data = []
    for prod in product_boxes:
        list_data.append({
            '대분류': prod.category or '',
            '시리즈': prod.series or '',
            '길이': '',
            '모델': prod.model or prod.sku,
            'sku': prod.sku,
            'name': prod.name,
            'l': prod.l,
            'w': prod.w,
            'h': prod.h,
            'weight': prod.weight or 0,
            'rotatable': prod.rotatable,
            'note': prod.note or ''
        })
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(pack_data).to_excel(writer, sheet_name='pack_boxes', index=False)
        pd.DataFrame(list_data).to_excel(writer, sheet_name='리스트', index=False)
    
    st.sidebar.download_button(
        label="💾 Download Excel",
        data=output.getvalue(),
        file_name="box_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# 현재 등록 통계
st.sidebar.markdown("---")
col1, col2 = st.sidebar.columns(2)
col1.metric("Packaging Boxes", len(storage.get_pack_boxes()))
col2.metric("Models", len(storage.get_product_boxes()))

catalog_status = st.session_state.get("catalog_status", {})
if catalog_status.get("product_sheet"):
    st.sidebar.caption(
        f"Product source: {catalog_status['product_sheet']} sheet"
    )
if catalog_status.get("skipped_product_rows"):
    st.sidebar.warning(
        f"{catalog_status['skipped_product_rows']} row(s) without valid box dimensions "
        "were excluded."
    )

# 시작 안내
st.info("👈 Select **Pack Simulator** or **Box Recommender** from the sidebar to get started!")
