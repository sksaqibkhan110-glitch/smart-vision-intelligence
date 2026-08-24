import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Smart Vision Intelligence | Edge AI SOC",
    page_icon="🛡️",
    layout="wide"
)

API_BASE_URL = "http://127.0.0.1:8000"

st.markdown("""
<style>
    .stApp { background-color: #0b0f19; color: #e2e8f0; }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-val { font-size: 28px; font-weight: 700; color: #38bdf8; }
    .metric-title { font-size: 13px; text-transform: uppercase; color: #94a3b8; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("🛡️ SOC Telemetry")
st.sidebar.caption("Spatial Threat & Identity Verification")
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Multi-Zone Calibration")

init_c_max, init_cr_min = 0.40, 0.60
try:
    zone_res = requests.get(f"{API_BASE_URL}/zones", timeout=2)
    if zone_res.status_code == 200:
        z_data = zone_res.json()
        init_c_max = float(z_data["zone1_caution"]["x_max"])
        init_cr_min = float(z_data["zone2_critical"]["x_min"])
except Exception:
    pass

caution_bound = st.sidebar.slider("Zone 1 (Yellow) Caution Bound", 0.10, 0.50, init_c_max, 0.05)
critical_bound = st.sidebar.slider("Zone 2 (Red) Critical Bound", 0.50, 0.90, init_cr_min, 0.05)

if st.sidebar.button("💾 Apply Zone Boundaries", use_container_width=True):
    requests.post(f"{API_BASE_URL}/zones", json={"caution_max": caution_bound, "critical_min": critical_bound})
    st.sidebar.success("Updated!")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔴 Live Vision Feed", 
    "📊 Threat Analytics", 
    "📁 Security Logs",
    "👤 Member Enrollment"
])

with tab1:
    col_stream, col_legend = st.columns([3, 1])
    with col_stream:
        st.markdown(
            f'<div style="border: 2px solid #334155; border-radius: 8px; overflow: hidden;">'
            f'<img src="{API_BASE_URL}/video_feed" width="100%" />'
            f'</div>',
            unsafe_allow_html=True
        )
    with col_legend:
        st.markdown("#### Threat Matrix")
        st.markdown("""
        <div style="background:#1e293b; padding:10px; border-left:4px solid #eab308; margin-bottom:8px;">
            <b>Zone 1 (Yellow):</b><br/><span style="font-size:12px;color:#94a3b8;">Caution Tracking</span>
        </div>
        <div style="background:#1e293b; padding:10px; border-left:4px solid #ef4444; margin-bottom:8px;">
            <b>Zone 2 (Red):</b><br/><span style="font-size:12px;color:#94a3b8;">Critical Breach</span>
        </div>
        <div style="background:#1e293b; padding:10px; border-left:4px solid #22c55e;">
            <b>Secure Zone:</b><br/><span style="font-size:12px;color:#94a3b8;">Whitelisted Human</span>
        </div>
        """, unsafe_allow_html=True)

with tab2:
    st.markdown("### Threat Analytics")
    try:
        res = requests.get(f"{API_BASE_URL}/analytics", timeout=3)
        if res.status_code == 200:
            data = res.json().get("analytics", {})
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f'<div class="metric-card"><div class="metric-val">{data.get("total_alerts",0)}</div><div class="metric-title">Total Alerts</div></div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f'<div class="metric-card"><div class="metric-val">{data.get("threats_today",0)}</div><div class="metric-title">Breaches Today</div></div>', unsafe_allow_html=True)
            with c3:
                st.markdown(f'<div class="metric-card"><div class="metric-val" style="font-size:18px;">{data.get("last_alert_time","N/A")}</div><div class="metric-title">Last Alert</div></div>', unsafe_allow_html=True)
            
            breakdown = data.get("threat_breakdown", {})
            if breakdown:
                st.bar_chart(pd.DataFrame(list(breakdown.items()), columns=["Type", "Count"]).set_index("Type"))
    except Exception:
        st.warning("Analytics loading...")

with tab3:
    st.markdown("### Security Incident Logs")
    try:
        res = requests.get(f"{API_BASE_URL}/alerts?limit=20", timeout=3)
        if res.status_code == 200:
            records = res.json().get("alerts", [])
            if records:
                st.dataframe(pd.DataFrame(records), use_container_width=True)
            else:
                st.info("No security logs recorded yet.")
    except Exception as e:
        st.error(f"Error fetching logs: {e}")

with tab4:
    st.markdown("### 👤 Member Whitelist Enrollment")
    with st.form("enroll_form", clear_on_submit=True):
        name_in = st.text_input("Member Name (e.g. SAQIB)")
        img_upload = st.file_uploader("Upload Member Face Photo (.jpg / .png)", type=["jpg", "jpeg", "png"])
        submitted = st.form_submit_button("✅ Register Member")

        if submitted and name_in and img_upload:
            files = {"file": (f"{name_in}.jpg", img_upload.getvalue(), "image/jpeg")}
            r = requests.post(f"{API_BASE_URL}/register_member", data={"name": name_in}, files=files)
            if r.status_code == 200:
                st.success(f"Member **{name_in.upper()}** enrolled successfully!")
            else:
                st.error("Registration failed.")