import streamlit as st
import pandas as pd
import os
import math


# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="KisanBridge",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# CUSTOM CSS - light theme, readable text
# ============================================================
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
    }
    section[data-testid="stSidebar"] {
        background-color: #f7f9f8;
        border-right: 1px solid #e0e6e4;
    }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label {
        color: #1a3c34 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #1a3c34 !important;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a3c34;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #5a6b66;
        margin-bottom: 1.5rem;
        letter-spacing: 0.3px;
    }
    .section-header {
        font-size: 1.15rem;
        font-weight: 600;
        color: #1a3c34;
        margin-top: 1.5rem;
        margin-bottom: 0.6rem;
        border-bottom: 2px solid #e0e6e4;
        padding-bottom: 0.3rem;
    }
    .metric-card {
        background-color: #f7f9f8;
        border: 1px solid #e0e6e4;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
    .metric-label {
        font-size: 0.75rem;
        color: #6b7c77;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1a3c34;
    }
    .recommendation-box {
        background-color: #e8f4ee;
        border-left: 5px solid #2e7d5b;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }
    .recommendation-text {
        font-size: 1.05rem;
        color: #1a3c34;
        font-weight: 600;
    }
    .data-source-badge {
        background-color: #e8f4ee;
        border: 1px solid #b8dcc8;
        border-radius: 6px;
        padding: 0.6rem 0.8rem;
        font-size: 0.85rem;
        color: #1a3c34;
        margin-bottom: 0.5rem;
    }
    .explanation-box {
        background-color: #f0f4f8;
        border-left: 5px solid #3a5a80;
        border-radius: 6px;
        padding: 1rem 1.2rem;
        color: #2a3a48;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    .footer-note {
        font-size: 0.8rem;
        color: #8a9a94;
        margin-top: 2rem;
        text-align: center;
        border-top: 1px solid #e0e6e4;
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# HEADER
# ============================================================
st.markdown('<div class="main-title">KisanBridge</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-title">Post-Harvest Decision Support System &nbsp;|&nbsp; '
    'Nashik Tomato Farmers &nbsp;|&nbsp; Offline-First Architecture</div>',
    unsafe_allow_html=True
)

# ============================================================
# DATA LOADING (OFFLINE-FIRST)
# ============================================================
@st.cache_data
def load_weather():
    if os.path.exists("offline_weather.csv"):
        df = pd.read_csv("offline_weather.csv")
        return float(df.iloc[0]["temperature_c"]), "Local cache"
    return 28.0, "Default fallback"

@st.cache_data
def load_prices():
    if os.path.exists("offline_prices.csv"):
        return pd.read_csv("offline_prices.csv"), "Local cache"
    return pd.DataFrame([
        {"mandi": "Local Trader", "price_per_kg": 8.0, "distance_km": 0},
        {"mandi": "Lasalgaon APMC", "price_per_kg": 12.0, "distance_km": 30},
        {"mandi": "Pimpalgaon APMC", "price_per_kg": 22.5, "distance_km": 45},
        {"mandi": "Yeola APMC", "price_per_kg": 18.0, "distance_km": 60},
    ]), "Default fallback"

temp, temp_src = load_weather()
prices_df, price_src = load_prices()

# ============================================================
# SIDEBAR - INPUTS
# ============================================================
with st.sidebar:
    st.markdown('<div class="section-header">Harvest Details</div>', unsafe_allow_html=True)
    quantity = st.number_input("Quantity (kg)", 10, 1000, 100, step=10)
    hours = st.slider("Hours since harvest", 0, 48, 6)
    condition = st.selectbox(
        "Produce condition",
        ["Good", "Minor damage", "Visible spoilage"]
    )

    st.markdown('<div class="section-header">Group Pooling</div>', unsafe_allow_html=True)
    farmers = st.slider("Farmers pooling transport", 1, 10, 1)

    st.markdown('<div class="section-header">Data Source</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="data-source-badge">'
        f'Weather: {temp_src}<br>'
        f'Prices: {price_src}<br>'
        f'Temperature: {temp} C<br>'
        f'<small>Operates without internet connection</small>'
        f'</div>',
        unsafe_allow_html=True
    )

# ============================================================
# SPOILAGE MODEL
# ============================================================
cond_factor = {
    "Good": 1.0,
    "Minor damage": 1.25,
    "Visible spoilage": 1.8
}[condition]

decay = math.exp(-0.03 * hours * (temp / 25) * cond_factor)
spoilage = max(0.35, min(1.0, decay))

# ============================================================
# NRV ENGINE
# ============================================================
results = []
for _, row in prices_df.iterrows():
    transport = 5 * row["distance_km"]
    net = quantity * row["price_per_kg"] * spoilage - transport
    results.append({
        "Mandi": row["mandi"],
        "Price (Rs/kg)": row["price_per_kg"],
        "Distance (km)": int(row["distance_km"]),
        "Transport (Rs)": round(transport),
        "Net Revenue (Rs)": round(net),
    })

res_df = pd.DataFrame(results).sort_values("Net Revenue (Rs)", ascending=False)
best = res_df.iloc[0]

# ============================================================
# DECISION RESULT
# ============================================================
st.markdown('<div class="section-header">Decision Result</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Recommended Mandi</div>'
        f'<div class="metric-value">{best["Mandi"]}</div>'
        f'</div>', unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Net Revenue</div>'
        f'<div class="metric-value">Rs {best["Net Revenue (Rs)"]:,}</div>'
        f'</div>', unsafe_allow_html=True
    )
with c3:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Spoilage Factor</div>'
        f'<div class="metric-value">{spoilage:.2f}</div>'
        f'</div>', unsafe_allow_html=True
    )
with c4:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Move Within</div>'
        f'<div class="metric-value">{max(0, 24 - hours)} hrs</div>'
        f'</div>', unsafe_allow_html=True
    )

st.markdown(
    f'<div class="recommendation-box">'
    f'<div class="recommendation-text">Recommended: {best["Mandi"]} '
    f'&mdash; estimated net income Rs {best["Net Revenue (Rs)"]:,} '
    f'after transport and spoilage.</div>'
    f'</div>',
    unsafe_allow_html=True
)

# ============================================================
# MANDI COMPARISON
# ============================================================
st.markdown('<div class="section-header">Mandi Comparison</div>', unsafe_allow_html=True)
st.dataframe(res_df, use_container_width=True, hide_index=True)

# ============================================================
# GROUP HARVEST RESCUE
# ============================================================
st.markdown('<div class="section-header">Group Harvest Rescue</div>', unsafe_allow_html=True)

shared_cost = 500
per_farmer = shared_cost / farmers

pA, pB, pC = st.columns(3)
with pA:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Farmers Pooling</div>'
        f'<div class="metric-value">{farmers}</div>'
        f'</div>', unsafe_allow_html=True
    )
with pB:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Per-Farmer Transport</div>'
        f'<div class="metric-value">Rs {per_farmer:.0f}</div>'
        f'</div>', unsafe_allow_html=True
    )
with pC:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Savings vs Solo</div>'
        f'<div class="metric-value">Rs {shared_cost - per_farmer:.0f}</div>'
        f'</div>', unsafe_allow_html=True
    )

st.caption(
    f"One farmer pays Rs {shared_cost}. {farmers} farmer(s) pay "
    f"Rs {per_farmer:.0f} each. Pooling makes cold transport affordable."
)

# ============================================================
# CREDIT VS MIDDLEMAN
# ============================================================
st.markdown('<div class="section-header">Credit vs. Middleman</div>', unsafe_allow_html=True)

transport_needed = best["Transport (Rs)"]
credit_cost = transport_needed * 0.02
middleman_loss = quantity * 8 * 0.15

cA, cB = st.columns(2)
with cA:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Micro-Credit Cost</div>'
        f'<div class="metric-value">Rs {credit_cost:.0f}</div>'
        f'</div>', unsafe_allow_html=True
    )
with cB:
    st.markdown(
        f'<div class="metric-card">'
        f'<div class="metric-label">Middleman Discount Loss</div>'
        f'<div class="metric-value">Rs {middleman_loss:.0f}</div>'
        f'</div>', unsafe_allow_html=True
    )

if credit_cost < middleman_loss:
    st.success(f"Credit is cheaper by Rs {middleman_loss - credit_cost:.0f}")
else:
    st.warning(f"Middleman is cheaper by Rs {credit_cost - middleman_loss:.0f}")

# ============================================================
# EXPLANATION
# ============================================================
st.markdown('<div class="section-header">Why This Recommendation?</div>', unsafe_allow_html=True)

st.markdown(
    f'<div class="explanation-box">'
    f'With <b>{quantity} kg</b> of <b>{condition.lower()}</b> tomatoes, '
    f'<b>{hours} hours</b> since harvest, at <b>{temp} C</b>:<br><br>'
    f'&bull; Spoilage model predicts <b>{spoilage*100:.0f}% quality retention</b><br>'
    f'&bull; Best mandi is <b>{best["Mandi"]}</b> at Rs {best["Price (Rs/kg)"]}/kg<br>'
    f'&bull; After Rs {best["Transport (Rs)"]} transport, net is '
    f'<b>Rs {best["Net Revenue (Rs)"]:,}</b><br>'
    f'&bull; Move within <b>{max(0, 24 - hours)} hours</b> to avoid further loss'
    f'</div>',
    unsafe_allow_html=True
)

# ============================================================
# FOOTER
# ============================================================
st.markdown(
    '<div class="footer-note">'
    'KisanBridge Prototype &nbsp;|&nbsp; Cost rates, spoilage constants, and '
    'credit terms are simulated assumptions for demonstration.'
    '</div>',
    unsafe_allow_html=True
)