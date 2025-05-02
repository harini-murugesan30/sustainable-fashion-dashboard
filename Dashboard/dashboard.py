import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="FFNetBoost Ordering Dashboard", layout="wide")

st.title("🧠 FFNetBoost Ordering Assistant")
st.markdown("Smart and Sustainable product ordering decisions")

# --- Load predictions ---
@st.cache_data
def load_data():
    return pd.read_csv("ffnetboost_predictions.csv")

df = load_data()

# --- Sidebar filters ---
st.sidebar.header("🎯 Order Filters")
product_ids = sorted(df["Product_ID"].unique())
warehouses = sorted(df["Warehouse"].unique())
factories = sorted(df["Factory"].unique())

selected_filter_type = st.sidebar.radio("Filter by", ["Product", "Warehouse", "Factory"])

filtered = pd.DataFrame()
title_suffix = ""

if selected_filter_type == "Product":
    selected_product = st.sidebar.selectbox("Select Product", product_ids)
    selected_warehouse = st.sidebar.selectbox("Select Your Warehouse", warehouses)
    filtered = df[(df["Product_ID"] == selected_product) & (df["Warehouse"] == selected_warehouse)]
    title_suffix = f"for Product {selected_product} and Warehouse {selected_warehouse}"

elif selected_filter_type == "Warehouse":
    selected_warehouse = st.sidebar.selectbox("Select Warehouse", warehouses)
    filtered = df[df["Warehouse"] == selected_warehouse]
    title_suffix = f"for Warehouse {selected_warehouse}"

else:
    selected_factory = st.sidebar.selectbox("Select Factory", factories)
    filtered = df[df["Factory"] == selected_factory]
    title_suffix = f"for Factory {selected_factory}"

# --- Dynamic scoring weights ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔧 Adjust Scoring Weights")
w_demand = st.sidebar.slider("Weight: Demand", 0.0, 1.0, 0.2)
w_delay = st.sidebar.slider("Weight: Delay", 0.0, 1.0, 0.3)
w_sustain = st.sidebar.slider("Weight: Sustainability", 0.0, 1.0, 0.5)

if round(w_demand + w_delay + w_sustain, 2) != 1.0:
    st.sidebar.warning("⚠️ Weights must sum to 1.0 to apply scoring.")
    valid_weights = False
else:
    valid_weights = True

if filtered.empty:
    st.warning("⚠️ No matching records found for selected filters.")
    st.stop()

# --- Compute Score ---
if valid_weights:
    def compute_score(row):
        demand_score = row["Demand"] / filtered["Demand"].max()
        delay_score = 1 - row["Delay"] / filtered["Delay"].max()
        sustain_score = row["Sustainable_Order"]
        return w_demand * demand_score + w_delay * delay_score + w_sustain * sustain_score

    filtered["Score"] = filtered.apply(compute_score, axis=1)
    best_row = filtered.sort_values("Score", ascending=False).iloc[0]

# --- Display Options ---
display_df = filtered[["Factory", "Product_ID", "Warehouse", "Demand", "Delay", "Sustainable_Order"]].copy()
display_df.columns = ["Factory", "Product", "Warehouse", "Predicted Demand", "Shipping Delay (days)", "Sustainable Order (1=Yes)"]

if valid_weights:
    display_df["Score"] = filtered["Score"].round(2)

sort_col = st.selectbox("Sort Results By", display_df.columns)
display_df = display_df.sort_values(sort_col, ascending=("Delay" in sort_col or "Shipping" in sort_col))

# --- Dataframe ---
st.subheader(f"📊 FFNetBoost Predictions {title_suffix}")
st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

# --- Download Button ---
st.download_button(
    label="💾 Download Results as CSV",
    data=display_df.to_csv(index=False),
    file_name=f"filtered_recommendations.csv",
    mime="text/csv"
)

# --- Recommendation ---
if valid_weights:
    if selected_filter_type == "Factory":
        st.markdown(f"### ✅ Recommended Record for Factory {selected_factory}")
        st.success(
            f"Best combination from **Factory {best_row['Factory']}**:\n\n"
            f"- **Product:** {best_row['Product_ID']}\n"
            f"- **Warehouse:** {best_row['Warehouse']}\n"
            f"- **Score:** {best_row['Score']:.2f}\n"
            f"- **Demand:** {best_row['Demand']:.1f} units\n"
            f"- **Delay:** {best_row['Delay']:.1f} days\n"
            f"- **Sustainability:** {'Yes' if best_row['Sustainable_Order']==1 else 'No'}"
        )
    else:
        st.markdown(f"### ✅ Recommended Record {title_suffix}")
        st.success(
            f"**Factory {best_row['Factory']}** is recommended.\n\n"
            f"- **Score:** {best_row['Score']:.2f}\n"
            f"- **Product:** {best_row['Product_ID']}\n"
            f"- **Warehouse:** {best_row['Warehouse']}\n"
            f"- **Demand:** {best_row['Demand']:.1f} units\n"
            f"- **Delay:** {best_row['Delay']:.1f} days\n"
            f"- **Sustainability:** {'Yes' if best_row['Sustainable_Order']==1 else 'No'}"
        )

# --- Visual Charts ---
col1, col2 = st.columns(2)

with col1:
    fig_demand = px.bar(
        filtered.sort_values("Demand", ascending=False),
        x="Factory" if selected_filter_type != "Factory" else "Warehouse",
        y="Demand",
        color="Factory",
        title=f"📦 Predicted Demand {title_suffix}"
    )
    st.plotly_chart(fig_demand, use_container_width=True)

with col2:
    fig_delay = px.bar(
        filtered.sort_values("Delay"),
        x="Factory" if selected_filter_type != "Factory" else "Warehouse",
        y="Delay",
        color="Factory",
        title=f"⏱ Predicted Delay {title_suffix}"
    )
    st.plotly_chart(fig_delay, use_container_width=True)

# --- Pie Chart for Sustainability ---
sustain_count = filtered["Sustainable_Order"].map({1: "Sustainable", 0: "Not Sustainable"}).value_counts()
fig_sustain = px.pie(
    names=sustain_count.index,
    values=sustain_count.values,
    title="🌱 Sustainability Split",
    color=sustain_count.index,
    color_discrete_map={"Sustainable": "green", "Not Sustainable": "red"}
)
st.plotly_chart(fig_sustain, use_container_width=True)