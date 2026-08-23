import streamlit as st
import sqlite3
import pandas as pd
import os
import cv2
import tempfile
from src.stream_processor import StreamProcessor

st.set_page_config(page_title="Smart Vision Telemetry", layout="wide", page_icon="🛡️")

st.sidebar.title("Configuration")
mode = st.sidebar.selectbox("Select Input Stream", ["Dashboard & Logs", "Process Video File"])

db_path = "data/surveillance.db"

if mode == "Dashboard & Logs":
    st.title("🛡️ Smart Vision Telemetry System")
    
    if st.button("🔄 Refresh Data"):
        st.rerun()

    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        df = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
        conn.close()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Breach Events", len(df))
        col2.metric("System Health", "Operational 🟢")
        col3.metric("Monitored Streams", "1 Active Channel")

        st.markdown("---")

        if not df.empty:
            st.subheader("📊 Temporal Breach Distribution")
            df['datetime'] = pd.to_datetime(df['timestamp'])
            df['hour'] = df['datetime'].dt.hour
            hourly_data = df['hour'].value_counts().sort_index()
            st.bar_chart(hourly_data)

            st.subheader("📋 Recorded Logs")
            st.dataframe(df[["id", "timestamp", "object_name", "confidence"]], use_container_width=True)

            st.subheader("📸 Incident Visual Evidence")
            cols = st.columns(4)
            for i, r in df.head(8).iterrows():
                if os.path.exists(r["snapshot_path"]):
                    cols[i % 4].image(r["snapshot_path"], caption=f"{r['timestamp']} | Conf: {r['confidence']}")
        else:
            st.info("No breach events detected yet.")
    else:
        st.warning("Database not initialized.")

elif mode == "Process Video File":
    st.title("📹 Video File Analysis Engine")
    uploaded = st.sidebar.file_uploader("Upload CCTV footage (mp4/avi)", type=["mp4", "avi", "mov"])

    if uploaded:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(uploaded.read())
        
        if st.button("Run Anomaly Detection on File"):
            st.info("Processing stream... Check desktop pop-up window. Press 'q' to stop.")
            processor = StreamProcessor(source=temp_file.name)
            processor.start_pipeline()