import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Vision Sentinel SOC",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE = "http://127.0.0.1:8000"

st.title("🛡️ Smart Vision Security & Threat Telemetry")

tab1, tab2, tab3 = st.tabs(["🔴 Live Vision Feed", "📊 Threat Analytics", "📁 Security Logs"])

# Tab 1: Live Video Streaming Inside Browser
with tab1:
    st.subheader("Real-Time Multi-Zone Surveillance Feed")
    st.write("Edge YOLOv8 Detection with Graded Dual-Zone Threat Engine.")
    
    col_feed, col_status = st.columns([3, 1])
    
    with col_feed:
        st.markdown(
            f'<img src="{API_BASE}/video_feed" width="100%" style="border-radius: 8px; border: 2px solid #333;" />',
            unsafe_allow_html=True
        )
        
    with col_status:
        st.markdown("### Threat Matrix")
        st.info("**Zone 1 (Yellow):** Caution / Tracking Area")
        st.error("**Zone 2 (Red):** Critical Breach / Siren + Telegram Alert")
        st.success("**Secure Zone:** Normal State")

# Tab 2: Threat Analytics
with tab2:
    st.subheader("Threat Distribution Analytics")
    try:
        res = requests.get(f"{API_BASE}/analytics", timeout=5).json()
        if res:
            df = pd.DataFrame(list(res.items()), columns=["Threat Type", "Incident Count"])
            st.bar_chart(df.set_index("Threat Type"))
        else:
            st.info("No security incidents logged yet.")
    except Exception:
        st.warning("Backend API offline. Start FastAPI server.")

# Tab 3: Security Logs
with tab3:
    st.subheader("Recent Breach Audit Logs")
    try:
        res = requests.get(f"{API_BASE}/alerts?limit=15", timeout=5).json()
        alerts = res.get("alerts", [])
        if alerts:
            df = pd.DataFrame(alerts, columns=["ID", "Timestamp", "Threat Type", "Confidence", "Snapshot Path"])
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No breach records found.")
    except Exception:
        st.warning("Backend API offline.")