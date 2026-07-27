"""
Box Recommender 페이지
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.storage import DataStorage
from core.models import PaddingConfig
from core.product_catalog import (
    filter_products,
    parse_search_terms,
    product_label,
)
from core.packing import run_packing_simulation
from viz.plotly_3d import create_3d_visualization
import pandas as pd

st.set_page_config(page_title="Box Recommender", page_icon="🏆", layout="wide")

st.title("🏆 Box Recommender")
st.markdown("Find the most efficient packaging box for your product combination")

storage = DataStorage()


st.sidebar.header("🎁 Select Products")
product_boxes = storage.get_product_boxes()
if not product_boxes:
    st.error("No product boxes registered.")
    st.stop()

if "rec_selected_products" not in st.session_state:
    st.session_state.rec_selected_products = {}

search_text = st.sidebar.text_area(
    "🔎 Multi Search (Model / SKU / Product Box)",
    placeholder="예:\nQCML-1200\nQEL-300\nY-0194-KO",
    key="rec_search_text"
)

search_terms = parse_search_terms(search_text)
filtered_products = filter_products(product_boxes, search_terms)

if search_terms:
    st.sidebar.caption(f"Search results: {len(filtered_products)} products")
    if not filtered_products:
        st.sidebar.warning("No matching products found.")

product_options = {
    product_label(prod): prod
    for prod in filtered_products
}

default_selected = list(product_options.keys()) if search_terms else [
    label for label, prod in product_options.items()
    if prod.product_id in st.session_state.rec_selected_products
]

selected_labels = st.sidebar.multiselect(
    "Select products",
    options=list(product_options.keys()),
    default=default_selected,
    key="rec_multiselect_products"
)

selected_product_ids_now = {
    product_options[label].product_id for label in selected_labels
}

for product_id in list(st.session_state.rec_selected_products.keys()):
    if product_id not in selected_product_ids_now:
        del st.session_state.rec_selected_products[product_id]

st.sidebar.markdown("**Selected products and quantities:**")
if selected_labels:
    for label in selected_labels:
        prod = product_options[label]
        qty = st.sidebar.number_input(
            f"{prod.model or prod.sku} Qty",
            min_value=1,
            value=st.session_state.rec_selected_products.get(prod.product_id, 1),
            step=1,
            key=f"rec_qty_{prod.product_id}"
        )
        st.session_state.rec_selected_products[prod.product_id] = qty
else:
    st.sidebar.info("검색 후 제품을 선택하세요.")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Cushioning Margin")
padding_enabled = st.sidebar.toggle("Apply Cushioning", value=False, key="rec_padding_toggle")
padding_x = 0
padding_y = 0
padding_z = 0
if padding_enabled:
    st.sidebar.markdown("**Padding (mm):**")
    padding_x = st.sidebar.number_input("L-axis", min_value=0.0, value=20.0, step=1.0, key="rec_pad_x")
    padding_y = st.sidebar.number_input("W-axis", min_value=0.0, value=20.0, step=1.0, key="rec_pad_y")
    padding_z = st.sidebar.number_input("H-axis", min_value=0.0, value=20.0, step=1.0, key="rec_pad_z")

padding_config = PaddingConfig(
    enabled=padding_enabled,
    padding_x=padding_x,
    padding_y=padding_y,
    padding_z=padding_z
)

st.sidebar.markdown("---")
st.sidebar.header("📊 Ranking Criteria")
ranking_criteria = st.sidebar.radio(
    "Criteria",
    ["Highest Fill Efficiency", "Most Packed Items", "Complete Packing Priority"]
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Calculation Options")
num_trials = st.sidebar.slider("Search Attempts", min_value=5, max_value=30, value=10, step=5, key="rec_trials")
top_n = st.sidebar.slider("Show Top N Boxes", min_value=1, max_value=10, value=3, step=1)

if st.sidebar.button("🚀 Start Recommendation", type="primary", use_container_width=True):
    if not st.session_state.rec_selected_products:
        st.error("Please select at least one product.")
    else:
        product_selections = []
        for product_id, qty in st.session_state.rec_selected_products.items():
            prod = [p for p in product_boxes if p.product_id == product_id][0]
            product_selections.append((prod, qty))

        pack_boxes = storage.get_pack_boxes()
        if not pack_boxes:
            st.error("No packaging boxes registered.")
            st.stop()

        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, pack_box in enumerate(pack_boxes):
            status_text.text(f"Testing {pack_box.name}... ({idx+1}/{len(pack_boxes)})")
            try:
                result = run_packing_simulation(
                    pack_box,
                    product_selections,
                    padding_config,
                    num_trials
                )
                results.append(result)
            except ValueError:
                pass
            except Exception:
                pass
            progress_bar.progress((idx + 1) / len(pack_boxes))

        status_text.empty()
        progress_bar.empty()

        if not results:
            st.error("No suitable packaging boxes found. Please check cushioning settings.")
            st.stop()

        if ranking_criteria == "Highest Fill Efficiency":
            results.sort(key=lambda r: r.fill_ratio, reverse=True)
        elif ranking_criteria == "Most Packed Items":
            results.sort(key=lambda r: r.total_fitted_count, reverse=True)
        elif ranking_criteria == "Complete Packing Priority":
            results.sort(key=lambda r: (r.total_unfitted_count == 0, r.fill_ratio), reverse=True)

        st.session_state["recommender_results"] = results[:top_n]
        st.success(f"✅ Recommendation completed! Showing top {len(results[:top_n])} packaging boxes.")

if "recommender_results" in st.session_state:
    results = st.session_state["recommender_results"]

    st.markdown("### 🏅 Recommended Packaging Boxes")

    for rank, result in enumerate(results, 1):
        with st.expander(
            f"**Rank #{rank}** - {result.pack_box_name} | Fill: {result.fill_ratio*100:.2f}% | Packed: {result.total_fitted_count}",
            expanded=(rank == 1)
        ):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Packed Items", result.total_fitted_count)
            col2.metric("Fill Efficiency", f"{result.fill_ratio*100:.2f}%")
            col3.metric("Unpacked Items", result.total_unfitted_count)
            col4.metric("Remaining Volume", f"{result.remaining_volume:,.0f} mm³")

            st.markdown("#### Details")
            tab1, tab2 = st.tabs(["📋 Table", "🎨 3D View"])

            with tab1:
                if result.fitted_items:
                    type_count = {}
                    for item in result.fitted_items:
                        if item.product_id not in type_count:
                            type_count[item.product_id] = {
                                "Model": item.model or item.product_id,
                                "SKU": item.sku,
                                "Product Box": item.name,
                                "Packed": 0,
                            }
                        type_count[item.product_id]["Packed"] += 1
                    df_fitted = pd.DataFrame(list(type_count.values()))
                    st.dataframe(df_fitted, use_container_width=True, hide_index=True)

                if result.unfitted_items:
                    st.markdown("**Unpacked Products**")
                    df_unfitted = pd.DataFrame([
                        {
                            "Model": u["model"] or u["product_id"],
                            "SKU": u["sku"],
                            "Product Box": u["name"],
                            "Quantity": u["qty"],
                        }
                        for u in result.unfitted_items
                    ])
                    st.dataframe(df_unfitted, use_container_width=True, hide_index=True)

            with tab2:
                if result.fitted_items:
                    fig = create_3d_visualization(result)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No packed items to visualize.")

else:
    st.info("👈 Configure settings in the sidebar and click 'Start Recommendation'")
