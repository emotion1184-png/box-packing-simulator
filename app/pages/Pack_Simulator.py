# app/pages/Pack_Simulator.py
"""
Pack Simulator 페이지
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import DataStorage
from core.models import PaddingConfig
from core.packing import run_packing_simulation
from core.metrics import calculate_kpi
from viz.plotly_3d import create_3d_visualization
import pandas as pd
import io

st.set_page_config(page_title="Pack Simulator", page_icon="📊", layout="wide")

st.title("📊 Pack Simulator")
st.markdown("Calculate maximum packing capacity with optimal placement")

storage = DataStorage()

# 사이드바 입력
st.sidebar.header("📦 Select Packaging Box")
pack_boxes = storage.get_pack_boxes()
if not pack_boxes:
    st.error("No packaging boxes registered. Please add data from Home page.")
    st.stop()

pack_box_names = [b.name for b in pack_boxes]
selected_pack_name = st.sidebar.selectbox("Packaging Box", pack_box_names)
selected_pack_box = [b for b in pack_boxes if b.name == selected_pack_name][0]

# 포장박스 정보 표시
with st.sidebar.expander("📋 Box Info"):
    st.write(f"**Inner:** {selected_pack_box.inner_L}×{selected_pack_box.inner_W}×{selected_pack_box.inner_H}mm")
    st.write(f"**Outer:** {selected_pack_box.outer_L}×{selected_pack_box.outer_W}×{selected_pack_box.outer_H}mm")
    if selected_pack_box.max_weight:
        st.write(f"**Max Weight:** {selected_pack_box.max_weight}kg")

st.sidebar.markdown("---")
st.sidebar.header("🎁 Select Products")
product_boxes = storage.get_product_boxes()
if not product_boxes:
    st.error("No product boxes registered.")
    st.stop()

# 제품 선택 UI 개선 - 테이블 형태
st.sidebar.markdown("**Select products and quantities:**")

# 세션 상태 초기화
if 'selected_products' not in st.session_state:
    st.session_state.selected_products = {}

# 제품 선택 테이블
for prod in product_boxes:
    col1, col2 = st.sidebar.columns([3, 2])
    
    with col1:
        selected = st.checkbox(
            f"{prod.sku} - {prod.name}",
            key=f"check_{prod.sku}",
            value=prod.sku in st.session_state.selected_products
        )
    
    with col2:
        if selected:
            qty = st.number_input(
                "Qty",
                min_value=1,
                value=st.session_state.selected_products.get(prod.sku, 1),
                step=1,
                key=f"qty_{prod.sku}",
                label_visibility="collapsed"
            )
            st.session_state.selected_products[prod.sku] = qty
        else:
            if prod.sku in st.session_state.selected_products:
                del st.session_state.selected_products[prod.sku]

# 완충재 설정
st.sidebar.markdown("---")
st.sidebar.header("🛡️ Cushioning Margin")
padding_enabled = st.sidebar.toggle("Apply Cushioning", value=False)
padding_x = 0
padding_y = 0
padding_z = 0
if padding_enabled:
    st.sidebar.markdown("**Padding (mm):**")
    padding_x = st.sidebar.number_input("L-axis", min_value=0.0, value=20.0, step=1.0, key="pad_x")
    padding_y = st.sidebar.number_input("W-axis", min_value=0.0, value=20.0, step=1.0, key="pad_y")
    padding_z = st.sidebar.number_input("H-axis", min_value=0.0, value=20.0, step=1.0, key="pad_z")

padding_config = PaddingConfig(
    enabled=padding_enabled,
    padding_x=padding_x,
    padding_y=padding_y,
    padding_z=padding_z
)

# 탐색 옵션
st.sidebar.markdown("---")
st.sidebar.header("⚙️ Calculation Options")
num_trials = st.sidebar.slider("Search Attempts", min_value=5, max_value=50, value=10, step=5)

# 계산 버튼
if st.sidebar.button("🚀 Run Simulation", type="primary", use_container_width=True):
    if not st.session_state.selected_products:
        st.error("Please select at least one product.")
    else:
        product_selections = []
        for sku, qty in st.session_state.selected_products.items():
            prod = [p for p in product_boxes if p.sku == sku][0]
            product_selections.append((prod, qty))
        
        try:
            with st.spinner("Calculating optimal placement..."):
                result = run_packing_simulation(
                    selected_pack_box,
                    product_selections,
                    padding_config,
                    num_trials
                )
            st.session_state['sim_result'] = result
            st.success("✅ Calculation completed!")
        except ValueError as e:
            st.error(f"❌ Calculation error: {e}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")

# 결과 표시
if 'sim_result' in st.session_state:
    result = st.session_state['sim_result']
    kpi = calculate_kpi(result)
    
    # KPI 표시
    st.markdown("### 📈 Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Packed Items", kpi['total_fitted'])
    col2.metric("Fill Efficiency", f"{kpi['fill_ratio_pct']:.2f}%")
    col3.metric("Remaining Volume", f"{kpi['remaining_volume']:,.0f} mm³")
    col4.metric("Unpacked Items", kpi['total_unfitted'])
    
    st.markdown("---")
    
    # 탭
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Result Table", "🎨 3D View", "📍 Coordinates", "💾 Export"])
    
    with tab1:
        st.subheader("Packed Products (by type)")
        if result.fitted_items:
            # 타입별 집계
            type_count = {}
            for item in result.fitted_items:
                if item.sku not in type_count:
                    type_count[item.sku] = {'SKU': item.sku, 'Product': item.name, 'Packed': 0}
                type_count[item.sku]['Packed'] += 1
            df_fitted = pd.DataFrame(list(type_count.values()))
            st.dataframe(df_fitted, use_container_width=True, hide_index=True)
        else:
            st.info("No items could be packed.")
        
        st.subheader("Unpacked Products")
        if result.unfitted_items:
            df_unfitted = pd.DataFrame([
                {'SKU': u['sku'], 'Product': u['name'], 'Quantity': u['qty']}
                for u in result.unfitted_items
            ])
            st.dataframe(df_unfitted, use_container_width=True, hide_index=True)
        else:
            st.success("All products were packed successfully!")
    
    with tab2:
        st.subheader("3D Visualization")
        if result.fitted_items:
            fig = create_3d_visualization(result)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No visualization available.")
    
    with tab3:
        st.subheader("Detailed Coordinates")
        if result.fitted_items:
            detail_data = []
            for item in result.fitted_items:
                detail_data.append({
                    'SKU': item.sku,
                    'Product': item.name,
                    'Position (x,y,z)': f"({item.position[0]:.1f}, {item.position[1]:.1f}, {item.position[2]:.1f})",
                    'Dimension (l,w,h)': f"({item.dimension[0]:.1f}, {item.dimension[1]:.1f}, {item.dimension[2]:.1f})",
                    'Rotation': item.rotation_type
                })
            df_detail = pd.DataFrame(detail_data)
            st.dataframe(df_detail, use_container_width=True, hide_index=True)
        else:
            st.info("No detail information available.")
    
    with tab4:
        st.subheader("Export Results")
        
        col1, col2 = st.columns(2)
        
        # CSV 다운로드
        with col1:
            if result.fitted_items:
                csv_data = []
                for item in result.fitted_items:
                    csv_data.append({
                        'SKU': item.sku,
                        'Product': item.name,
                        'Pos_X': item.position[0],
                        'Pos_Y': item.position[1],
                        'Pos_Z': item.position[2],
                        'Dim_L': item.dimension[0],
                        'Dim_W': item.dimension[1],
                        'Dim_H': item.dimension[2],
                        'Rotation': item.rotation_type
                    })
                df_csv = pd.DataFrame(csv_data)
                csv_buffer = io.StringIO()
                df_csv.to_csv(csv_buffer, index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_buffer.getvalue(),
                    file_name="packing_result.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
        # HTML 다운로드 (3D 포함)
        with col2:
            if result.fitted_items:
                fig = create_3d_visualization(result)
                html_str = fig.to_html(include_plotlyjs='cdn')
                st.download_button(
                    label="📥 Download HTML (3D)",
                    data=html_str,
                    file_name="packing_3d.html",
                    mime="text/html",
                    use_container_width=True
                )

else:
    st.info("👈 Configure settings in the sidebar and click 'Run Simulation'")
