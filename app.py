import streamlit as st
import pandas as pd
import requests
from streamlit_drawable_canvas import st_canvas

st.set_page_config(
    page_title="Smart Vision Intelligence | Edge AI SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = "http://127.0.0.1:8000"

st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
    }
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
    }
    .metric-val {
        font-size: 28px;
        font-weight: 700;
        color: #38bdf8;
    }
    .metric-title {
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #94a3b8;
    }
    .flash-feed {
        border: 3px solid #ef4444 !important;
        box-shadow: 0 0 25px rgba(239, 68, 68, 0.6);
        animation: pulseBorder 1.5s infinite;
    }
    @keyframes pulseBorder {
        0% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
        50% { box-shadow: 0 0 30px rgba(239, 68, 68, 0.85); }
        100% { box-shadow: 0 0 10px rgba(239, 68, 68, 0.4); }
    }
</style>
""", unsafe_allow_html=True)

# Sidebar - Video Routing & Boundary Telemetry
st.sidebar.image("https://img.icons8.com/isometric/512/cctv.png", width=70)
st.sidebar.title("🛡️ SOC Telemetry")
st.sidebar.caption("Smart Spatial Threat & Identity Verification")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📹 Video Source Routing")

cam_choice = st.sidebar.selectbox(
    "Select Camera Channel:",
    ["Default USB Cam (0)", "Secondary USB Cam (1)", "Custom IP / RTSP URL"]
)

custom_url = ""
if cam_choice == "Custom IP / RTSP URL":
    custom_url = st.sidebar.text_input("Stream URL:", placeholder="http://192.168.1.X:8080/video")

if st.sidebar.button("🔄 Switch Camera Stream", use_container_width=True):
    target_src = "0"
    if "0" in cam_choice:
        target_src = "0"
    elif "1" in cam_choice:
        target_src = "1"
    elif custom_url:
        target_src = custom_url

    try:
        res = requests.post(f"{API_BASE_URL}/switch_camera", json={"source": target_src}, timeout=4)
        if res.status_code == 200:
            st.sidebar.success(f"Connected to Source: {target_src}")
        else:
            st.sidebar.error("Failed to switch source.")
    except Exception as e:
        st.sidebar.error(f"Switch Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Quick Linear Boundaries")

init_c_max, init_cr_min = 0.40, 0.60
try:
    zone_res = requests.get(f"{API_BASE_URL}/zones", timeout=2)
    if zone_res.status_code == 200:
        z_data = zone_res.json()
        init_c_max = float(z_data["zone1_caution"].get("x_max", 0.40))
        init_cr_min = float(z_data["zone2_critical"].get("x_min", 0.60))
except Exception:
    pass

caution_bound = st.sidebar.slider(
    "Zone 1 (Yellow) Caution Bound [X-Max]",
    min_value=0.10,
    max_value=0.50,
    value=init_c_max,
    step=0.05
)

critical_bound = st.sidebar.slider(
    "Zone 2 (Red) Critical Bound [X-Min]",
    min_value=0.50,
    max_value=0.90,
    value=init_cr_min,
    step=0.05
)

if st.sidebar.button("💾 Apply Linear Boundaries", use_container_width=True):
    payload = {"caution_max": caution_bound, "critical_min": critical_bound}
    try:
        res = requests.post(f"{API_BASE_URL}/zones", json=payload, timeout=3)
        if res.status_code == 200:
            st.sidebar.success("Boundaries Live-Updated!")
        else:
            st.sidebar.error("Failed to update boundaries.")
    except Exception as e:
        st.sidebar.error(f"Connection Error: {e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 📡 Engine Telemetry")
st.sidebar.info(
    "• High-FPS Interpolated Inference\n"
    "• Multi-Source: RTSP / IP / USB Dynamic\n"
    "• Biometrics: Individual Facial Spatial Grid\n"
    "• Threat Escalation: Persistent Caution & Instant Critical"
)

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔴 Live Vision Feed", 
    "📊 Threat Analytics", 
    "📁 Security Logs",
    "👤 Member Enrollment",
    "📐 Interactive Zone Drawer"
])

# Tab 1: Live Stream with Browser Alerts
with tab1:
    st.markdown("### Real-Time Multi-Zone Surveillance Feed")
    st.caption("Edge YOLOv8 Detection with Dual-Zone Spatial Threat Escalation.")

    col_stream, col_legend = st.columns([3, 1])

    with col_stream:
        st.markdown(
            f'<div class="flash-feed" style="border-radius: 8px; overflow: hidden;">'
            f'<img src="{API_BASE_URL}/video_feed" width="100%" />'
            f'</div>',
            unsafe_allow_html=True
        )

    with col_legend:
        st.markdown("#### Threat Matrix")
        st.markdown("""
        <div style="background-color: #1e293b; padding: 12px; border-left: 5px solid #eab308; border-radius: 4px; margin-bottom: 8px;">
            <b style="color: #38bdf8;">Zone 1 (Yellow):</b><br/>
            <span style="font-size: 13px; color: #94a3b8;">Caution / 3s Countdown & Persistent Alert</span>
        </div>
        <div style="background-color: #1e293b; padding: 12px; border-left: 5px solid #ef4444; border-radius: 4px; margin-bottom: 8px;">
            <b style="color: #ef4444;">Zone 2 (Red):</b><br/>
            <span style="font-size: 13px; color: #94a3b8;">Critical Breach / Instant Siren + Snapshot</span>
        </div>
        <div style="background-color: #1e293b; padding: 12px; border-left: 5px solid #22c55e; border-radius: 4px; margin-bottom: 8px;">
            <b style="color: #22c55e;">Secure Zone:</b><br/>
            <span style="font-size: 13px; color: #94a3b8;">Normal State / Whitelisted Human</span>
        </div>
        <div style="background-color: #1e293b; padding: 12px; border-left: 5px solid #06b6d4; border-radius: 4px;">
            <b style="color: #06b6d4;">Liveness Verification:</b><br/>
            <span style="font-size: 13px; color: #94a3b8;">Anti-Spoofing Micro-Motion & Blink Check</span>
        </div>
        """, unsafe_allow_html=True)

# Tab 2: Threat Analytics
with tab2:
    st.markdown("### Threat Analytics & Audit Metrics")
    try:
        analytics_res = requests.get(f"{API_BASE_URL}/analytics", timeout=3)
        if analytics_res.status_code == 200:
            data = analytics_res.json().get("analytics", {})
            
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{data.get('total_alerts', 0)}</div>
                    <div class="metric-title">Total Security Alerts</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val">{data.get('threats_today', 0)}</div>
                    <div class="metric-title">Critical Breaches Today</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                last_ts = data.get('last_alert_time', 'N/A')
                st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-val" style="font-size: 18px; line-height: 28px;">{last_ts.split()[1] if ' ' in str(last_ts) else last_ts}</div>
                    <div class="metric-title">Last Trigger Timestamp</div>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### Incident Frequency Breakdown")
            breakdown = data.get("threat_breakdown", {})
            if breakdown:
                df_chart = pd.DataFrame(list(breakdown.items()), columns=["Threat Type", "Count"])
                st.bar_chart(df_chart.set_index("Threat Type"))
            else:
                st.info("No recorded breach data available for graphical metrics.")
        else:
            st.error("Failed to load metrics from API.")
    except Exception as e:
        st.error(f"Cannot reach Analytics Backend: {e}")

# Tab 3: Security Logs
with tab3:
    st.markdown("### Security Incident Audit Logs")
    st.caption("Immutable SQLite event ledger synced with automated edge snapshots.")
    
    try:
        alerts_res = requests.get(f"{API_BASE_URL}/alerts?limit=25", timeout=3)
        if alerts_res.status_code == 200:
            records = alerts_res.json().get("alerts", [])
            if records:
                df_logs = pd.DataFrame(records)
                st.dataframe(df_logs, use_container_width=True)
            else:
                st.info("No breach alerts logged in the ledger yet.")
        else:
            st.error("Failed to fetch alert logs from backend.")
    except Exception as e:
        st.error(f"Ledger Sync Error: {e}")

# Tab 4: Member Enrollment
with tab4:
    st.markdown("### 👤 Authorized Personnel Enrollment")
    st.caption("Register new authorized members directly to the edge face engine whitelist.")

    with st.form("enrollment_form", clear_on_submit=True):
        member_name = st.text_input("Enter Member Name (e.g. SAQIB)")
        img_upload = st.file_uploader("Upload Member Face Photo (.jpg / .png)", type=["jpg", "jpeg", "png"])
        submit_btn = st.form_submit_button("✅ Register Member")

        if submit_btn:
            if not member_name or not img_upload:
                st.warning("Please provide both a member name and a face photo.")
            else:
                files = {"file": (f"{member_name}.jpg", img_upload.getvalue(), "image/jpeg")}
                data = {"name": member_name}
                try:
                    res = requests.post(f"{API_BASE_URL}/register_member", data=data, files=files, timeout=5)
                    if res.status_code == 200:
                        st.success(f"Member **{member_name.upper()}** successfully authorized & whitelisted!")
                    else:
                        st.error("Failed to register member.")
                except Exception as e:
                    st.error(f"Backend unreachable: {e}")

# Tab 5: Interactive Custom Zone Drawer
with tab5:
    st.markdown("### 📐 Interactive Custom Zone Selector")
    st.caption("Drag your mouse directly on the canvas below to draw a custom bounding zone box.")

    zone_mode = st.radio("Select Target Zone to Draw:", ["Zone 1 (Yellow - Caution)", "Zone 2 (Red - Critical)"], horizontal=True)
    stroke_color = "#eab308" if "Yellow" in zone_mode else "#ef4444"

    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.15)",
        stroke_width=3,
        stroke_color=stroke_color,
        background_color="#1e293b",
        height=480,
        width=640,
        drawing_mode="rect",
        key="zone_canvas_rect",
    )

    if st.button("💾 Save Drawn Zone to System", use_container_width=True):
        if canvas_result.json_data is not None:
            objects = canvas_result.json_data.get("objects", [])
            z1_poly, z2_poly = [], []
            for obj in objects:
                left = int(obj.get("left", 0))
                top = int(obj.get("top", 0))
                w_box = int(obj.get("width", 0))
                h_box = int(obj.get("height", 0))
                
                poly = [
                    [left, top],
                    [left + w_box, top],
                    [left + w_box, top + h_box],
                    [left, top + h_box]
                ]
                
                if "Yellow" in zone_mode:
                    z1_poly = poly
                else:
                    z2_poly = poly

            payload = {"zone1_poly": z1_poly, "zone2_poly": z2_poly}
            try:
                res = requests.post(f"{API_BASE_URL}/zones_polygon", json=payload, timeout=3)
                if res.status_code == 200:
                    st.success("✅ Custom Zone Saved & Live-Applied to Edge Vision!")
                else:
                    st.error("Failed to save zone.")
            except Exception as e:
                st.error(f"Connection Error: {e}")