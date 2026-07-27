"""
Packing Plan 페이지 - 전체 제품을 담기 위한 포장박스 조합 계산
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
from core.packing_plan import get_multiple_packing_plans
import pandas as pd

st.set_page_config(page_title="Packing Plan", page_icon="📋", layout="wide")

st.title("📋 Packing Plan")
st.markdown("Calculate how many packaging boxes you need for all your products")

storage = DataStorage()


st.sidebar.header("🎁 Product Requirements")
product_boxes = storage.get_product_boxes()
if not product_boxes:
    st.error("No product boxes registered.")
    st.stop()

if "plan_products" not in st.session_state:
    st.session_state.plan_products = {}

search_text = st.sidebar.text_area(
    "🔎 Multi Search (Model / SKU / Product Box)",
    placeholder="예:\nQCML-1200\nQEL-300\nY-0194-KO",
    key="plan_search_text"
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
    if prod.product_id in st.session_state.plan_products
]

selected_labels = st.sidebar.multiselect(
    "Select products",
    options=list(product_options.keys()),
    default=default_selected,
    key="plan_multiselect_products"
)

selected_product_ids_now = {
    product_options[label].product_id for label in selected_labels
}

for product_id in list(st.session_state.plan_products.keys()):
    if product_id not in selected_product_ids_now:
        del st.session_state.plan_products[product_id]

st.sidebar.markdown("**Enter total quantity for selected products:**")
if selected_labels:
    for label in selected_labels:
        prod = product_options[label]
        qty = st.sidebar.number_input(
            f"{prod.model or prod.sku} Total",
            min_value=1,
            value=st.session_state.plan_products.get(prod.product_id, 10),
            step=1,
            key=f"plan_qty_{prod.product_id}"
        )
        st.session_state.plan_products[prod.product_id] = qty
else:
    st.sidebar.info("검색 후 제품을 선택하세요.")

st.sidebar.markdown("---")
st.sidebar.header("🛡️ Cushioning Margin")
padding_enabled = st.sidebar.toggle("Apply Cushioning", value=False, key="plan_padding_toggle")
padding_x = 0
padding_y = 0
padding_z = 0
if padding_enabled:
    st.sidebar.markdown("**Padding (mm):**")
    padding_x = st.sidebar.number_input("L-axis", min_value=0.0, value=20.0, step=1.0, key="plan_pad_x")
    padding_y = st.sidebar.number_input("W-axis", min_value=0.0, value=20.0, step=1.0, key="plan_pad_y")
    padding_z = st.sidebar.number_input("H-axis", min_value=0.0, value=20.0, step=1.0, key="plan_pad_z")

padding_config = PaddingConfig(
    enabled=padding_enabled,
    padding_x=padding_x,
    padding_y=padding_y,
    padding_z=padding_z
)

st.sidebar.markdown("---")
st.sidebar.header("⚙️ Calculation Options")
num_trials = st.sidebar.slider("Search Attempts", min_value=5, max_value=30, value=10, step=5, key="plan_trials")

if st.sidebar.button("🚀 Calculate Plan", type="primary", use_container_width=True):
    if not st.session_state.plan_products:
        st.error("Please select at least one product and enter quantity.")
    else:
        product_requirements = []
        total_items = 0
        for product_id, qty in st.session_state.plan_products.items():
            prod = [p for p in product_boxes if p.product_id == product_id][0]
            product_requirements.append((prod, qty))
            total_items += qty

        pack_boxes = storage.get_pack_boxes()
        if not pack_boxes:
            st.error("No packaging boxes registered.")
            st.stop()

        with st.spinner(f"Calculating optimal packing plan for {total_items} items..."):
            plans = get_multiple_packing_plans(
                product_requirements,
                pack_boxes,
                padding_config,
                num_trials
            )

        if not plans:
            st.error("Could not generate any packing plan. Please check your settings.")
            st.stop()

        st.session_state["packing_plans"] = plans
        st.session_state["product_requirements"] = product_requirements
        st.success(f"✅ Calculation completed! Found {len(plans)} strategy options.")

if "packing_plans" in st.session_state:
    plans = st.session_state["packing_plans"]
    product_requirements = st.session_state["product_requirements"]

    st.markdown("### 📦 Product Requirements")
    req_data = []
    for prod, qty in product_requirements:
        req_data.append({
            "Model": prod.model or prod.product_id,
            "SKU": prod.sku,
            "Product Box": prod.name,
            "Total Quantity": qty,
            "Size (L×W×H)": f"{prod.l}×{prod.w}×{prod.h}mm"
        })
    df_req = pd.DataFrame(req_data)
    st.dataframe(df_req, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🎯 Recommended Packing Plans")

    for idx, (strategy_name, plan) in enumerate(plans, 1):
        with st.expander(f"**Strategy {idx}: {strategy_name}**", expanded=(idx == 1)):
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total Boxes Needed", plan.total_boxes)
            col2.metric("All Packed", "✅ Yes" if plan.all_packed else "❌ No")
            col3.metric("Total Volume", f"{plan.total_volume:,.0f} mm³")

            avg_efficiency = sum([r.fill_ratio for r in plan.packed_details]) / len(plan.packed_details) if plan.packed_details else 0
            col4.metric("Avg Fill Efficiency", f"{avg_efficiency*100:.1f}%")

            st.markdown("#### 📦 Box Usage Breakdown")
            usage_data = []
            for box_name, count in plan.box_usage.items():
                usage_data.append({
                    "Packaging Box": box_name,
                    "Quantity Needed": count
                })
            df_usage = pd.DataFrame(usage_data)
            st.dataframe(df_usage, use_container_width=True, hide_index=True)

            if st.checkbox(f"Show detailed packing for each box (Strategy {idx})", key=f"detail_{idx}"):
                st.markdown("#### 📋 Detailed Packing List")
                for box_idx, result in enumerate(plan.packed_details, 1):
                    st.markdown(f"**Box #{box_idx}: {result.pack_box_name}**")

                    if result.fitted_items:
                        type_count = {}
                        for item in result.fitted_items:
                            if item.product_id not in type_count:
                                type_count[item.product_id] = {
                                    "Model": item.model or item.product_id,
                                    "SKU": item.sku,
                                    "Product Box": item.name,
                                    "Qty": 0,
                                }
                            type_count[item.product_id]["Qty"] += 1

                        df_box = pd.DataFrame(list(type_count.values()))
                        st.dataframe(df_box, use_container_width=True, hide_index=True)
                    else:
                        st.info("Empty box")

                    st.markdown("---")

else:
    st.info("👈 Configure product requirements in the sidebar and click 'Calculate Plan'")

    st.markdown("### 💡 Example Use Case")
    st.markdown("""
    **Scenario:** You need to pack:
    - Product A: 100 units
    - Product B: 50 units
    - Product C: 30 units

    **This tool will calculate:**
    - How many packaging boxes you need
    - Which box types to use
    - How many of each box type
    - Detailed packing list for each box

    **Multiple strategies:**
    1. **Minimize Box Count**: Uses fewest boxes possible
    2. **Maximize Efficiency**: Optimizes space utilization
    """)
