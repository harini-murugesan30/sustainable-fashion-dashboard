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

# --- Aggregate to one row per Factory–Product–Warehouse ---
agg_df = (
    df.groupby(["Factory", "Product_ID", "Warehouse"], as_index=False)
    .agg({
        "Demand": "sum",
        "Delay": "mean",
        "Sustainable_Order": "mean"
    })
    .assign(Sustainable_Order=lambda d: (d.Sustainable_Order * 100).round(1))
)
df = agg_df

# --- Sidebar filters ---
st.sidebar.header("🎯 Order Filters")
product_ids = sorted(df["Product_ID"].unique())
warehouses = sorted(df["Warehouse"].unique())
factories = sorted(df["Factory"].unique())

selected_filter_type = st.sidebar.radio("Filter by", ["Product", "Warehouse", "Factory"])

if selected_filter_type == "Product":
    selected_product = st.sidebar.selectbox("Select Product", product_ids)
    filtered = df[df["Product_ID"] == selected_product]
    title_suffix = f"for Product {selected_product}"

elif selected_filter_type == "Warehouse":
    selected_warehouse = st.sidebar.selectbox("Select Warehouse", warehouses)
    filtered = df[df["Warehouse"] == selected_warehouse]
    title_suffix = f"for Warehouse {selected_warehouse}"

else:
    selected_factory = st.sidebar.selectbox("Select Factory", factories)
    filtered = df[df["Factory"] == selected_factory]
    title_suffix = f"for Factory {selected_factory}"

# --- How many top recommendations? ---
st.sidebar.markdown("---")
top_n = st.sidebar.number_input(
    "How many top recommendations?", 
    min_value=1, 
    max_value=len(filtered), 
    value=1, 
    step=1
)

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
        sustain_score = row["Sustainable_Order"] / 100  # convert percent back to 0–1
        return w_demand * demand_score + w_delay * delay_score + w_sustain * sustain_score

    filtered["Score"] = filtered.apply(compute_score, axis=1)
    # get the top N
    top_recs = filtered.sort_values("Score", ascending=False).head(top_n)
    best_row = top_recs.iloc[0]

# --- Display full results table ---
display_df = filtered[["Product_ID", "Factory", "Warehouse", "Demand", "Delay", "Sustainable_Order"]].copy()
display_df.columns = [
    "Product", "Factory", "Warehouse", 
    "Predicted Demand", "Shipping Delay (days)", 
    "Sustainability (%)"
]
if valid_weights:
    display_df["Score"] = filtered["Score"].round(2)

sort_col = st.selectbox("Sort Results By", display_df.columns)
ascending = not ("Delay" in sort_col or "Shipping" in sort_col)
display_df = display_df.sort_values(sort_col, ascending=ascending)

st.subheader(f"📊 FFNetBoost Predictions {title_suffix}")
st.dataframe(display_df.reset_index(drop=True), use_container_width=True)

# --- Download Button ---
st.download_button(
    label="💾 Download Results as CSV",
    data=display_df.to_csv(index=False),
    file_name="filtered_recommendations.csv",
    mime="text/csv"
)

# --- Enhanced Recommendations ---
if valid_weights:
    if top_n == 1:
        # 1) Show key metrics at a glance
        best = best_row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Score", f"{best.Score:.2f}")
        m2.metric("Demand", f"{best.Demand:.0f}")
        m3.metric("Delay", f"{best.Delay:.1f} days")
        m4.metric("Sustainability", f"{best.Sustainable_Order:.1f}%")
        st.markdown(
            f"**Factory:** {best.Factory}  |  "
            f"**Product:** {best.Product_ID}  |  "
            f"**Warehouse:** {best.Warehouse}"
        )

        # 2) Breakdown of score components
        st.subheader("🔍 Score Breakdown")
        demand_part  = w_demand  * (best.Demand  / filtered["Demand"].max())
        delay_part   = w_delay   * (1 - best.Delay / filtered["Delay"].max())
        sustain_part = w_sustain * (best.Sustainable_Order / 100)
        st.write(f"- Demand component: **{demand_part:.2f}**")
        st.write(f"- Delay component: **{delay_part:.2f}**")
        st.write(f"- Sustainability component: **{sustain_part:.2f}**")

    else:
        st.markdown(f"### ✅ Top {top_n} Recommendations {title_suffix}")
        recs = top_recs[[
            "Product_ID", "Factory", "Warehouse", 
            "Demand", "Delay", "Sustainable_Order", "Score"
        ]].rename(columns={
            "Product_ID":"Product",
            "Demand":"Demand (units)",
            "Delay":"Delay (days)",
            "Sustainable_Order":"Sustainability (%)"
        })
        recs["Score"] = recs.Score.round(2)
        recs["Sustainability (%)"] = recs["Sustainability (%)"].round(1)
        st.table(recs.reset_index(drop=True))

# --- Visual Charts (faceted by Factory, colored by Warehouse) ---
col1, col2 = st.columns(2)

with col1:
    fig_demand = px.bar(
        filtered.sort_values("Demand", ascending=False),
        x="Product_ID",
        y="Demand",
        color="Warehouse",
        facet_col="Factory",
        category_orders={
            "Product_ID": sorted(filtered["Product_ID"].unique()),
            "Factory": sorted(filtered["Factory"].unique())
        },
        title=f"📦 Predicted Demand {title_suffix}"
    )
    fig_demand.update_layout(
        xaxis_title="Product",
        yaxis_title="Predicted Demand",
        legend_title="Warehouse",
        margin=dict(t=50, b=50)
    )
    st.plotly_chart(fig_demand, use_container_width=True)

with col2:
    fig_delay = px.bar(
        filtered.sort_values("Delay"),
        x="Product_ID",
        y="Delay",
        color="Warehouse",
        facet_col="Factory",
        category_orders={
            "Product_ID": sorted(filtered["Product_ID"].unique()),
            "Factory": sorted(filtered["Factory"].unique())
        },
        title=f"⏱ Predicted Delay {title_suffix}"
    )
    fig_delay.update_layout(
        xaxis_title="Product",
        yaxis_title="Shipping Delay (days)",
        legend_title="Warehouse",
        margin=dict(t=50, b=50)
    )
    st.plotly_chart(fig_delay, use_container_width=True)

# --- Pie Chart for Sustainability (raw 0/1 counts) ---
orig = load_data()
orig_filtered = orig.merge(
    filtered[["Factory", "Product_ID", "Warehouse"]],
    on=["Factory", "Product_ID", "Warehouse"],
    how="inner"
)
sustain_count = orig_filtered["Sustainable_Order"] \
    .map({1: "Sustainable", 0: "Not Sustainable"}) \
    .value_counts()
fig_sustain = px.pie(
    names=sustain_count.index,
    values=sustain_count.values,
    title="🌱 Sustainability Split",
    color=sustain_count.index,
    color_discrete_map={"Sustainable": "green", "Not Sustainable": "red"}
)
st.plotly_chart(fig_sustain, use_container_width=True)
