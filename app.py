import streamlit as st
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="Smart Vision Intelligence", layout="wide", page_icon="🛡️")

st.title("🛡️ Smart Vision Intelligence — Security Dashboard")
st.markdown("Real-time automated incident tracking, detection analytics & snapshot logs.")

db_path = "data/surveillance.db"

if st.button("🔄 Refresh Data"):
    st.rerun()

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
    conn.close()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Incidents Logged", len(df))
    col2.metric("System Status", "ACTIVE 🟢")
    col3.metric("Monitored Zones", "Zone-A (Webcam)")

    st.markdown("---")

    if not df.empty:
        # Chart Section using Pandas
        st.subheader("📊 Incident Frequency Breakdown")
        df['datetime'] = pd.to_datetime(df['timestamp'])
        df['hour'] = df['datetime'].dt.hour
        hourly_counts = df['hour'].value_counts().sort_index()
        
        st.bar_chart(hourly_counts)

        st.subheader("📋 Recent Security Logs")
        st.dataframe(df[["id", "timestamp", "object_name", "confidence"]], use_container_width=True)

        st.subheader("📸 Captured Incident Snapshots")
        cols = st.columns(4)
        for index, row in df.head(8).iterrows():
            if os.path.exists(row["snapshot_path"]):
                cols[index % 4].image(
                    row["snapshot_path"], 
                    caption=f"{row['timestamp']} | Conf: {row['confidence']}",
                    use_container_width=True
                )
    else:
        st.info("No incidents logged yet. Start detector to capture data.")
else:
    st.warning("Database not initialized yet. Run `python main.py` first to generate logs.")