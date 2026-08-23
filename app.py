import os
import time
import sqlite3
import pandas as pd
import streamlit as st
import cv2
import numpy as np
from ultralytics import YOLO

st.set_page_config(
    page_title="Smart Vision Operations Console",
    layout="wide",
    page_icon="🛡️"
)

DB_PATH = "data/surveillance.db"

@st.cache_resource
def load_model():
    return YOLO("yolov8n.pt")

detector = load_model()

st.sidebar.title("🛡️ System Control Panel")
app_mode = st.sidebar.radio("Navigation", ["Live Edge Monitor", "Telemetry & Logs", "Incident Analytics"])

min_conf = st.sidebar.slider("Detection Confidence Threshold", 0.1, 0.9, 0.45, 0.05)
enable_sound = st.sidebar.toggle("Enable Audio Siren", value=True)

if app_mode == "Live Edge Monitor":
    st.title("📹 Live Edge Camera Feed")
    st.caption("Real-time YOLOv8 spatial intrusion detection with web telemetry.")

    run_stream = st.checkbox("Start Live Feed", value=False)
    frame_placeholder = st.empty()
    status_placeholder = st.empty()

    if run_stream:
        cap = cv2.VideoCapture(0)
        roi = np.array([[300, 100], [620, 100], [620, 460], [300, 460]], np.int32)
        
        while run_stream and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                st.error("Failed to read from camera source.")
                break

            overlay = frame.copy()
            cv2.polylines(frame, [roi], True, (0, 0, 255), 2)
            cv2.fillPoly(overlay, [roi], (0, 0, 255))
            frame = cv2.addWeighted(overlay, 0.2, frame, 0.8, 0)

            results = detector(frame, conf=min_conf, verbose=False)
            breach = False

            for res in results:
                frame = res.plot()
                for box in res.boxes:
                    label = detector.names[int(box.cls[0])]
                    if label == "person":
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        feet = (int((x1 + x2) / 2), y2)
                        if cv2.pointPolygonTest(roi, feet, False) >= 0:
                            breach = True

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(frame_rgb, channels="RGB", use_container_width=True)

            if breach:
                status_placeholder.error("🚨 CRITICAL WARNING: Active Intrusion Detected in Restricted Zone!")
            else:
                status_placeholder.success("🟢 System Nominal: Secure Zone Clear")

            time.sleep(0.03)

        cap.release()

elif app_mode == "Telemetry & Logs":
    st.title("📋 Incident Forensic Records")

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM alerts ORDER BY id DESC", conn)
        conn.close()

        if not df.empty:
            st.download_button(
                label="📥 Export Logs as CSV",
                data=df.to_csv(index=False),
                file_name="security_incidents_report.csv",
                mime="text/csv",
            )

            st.dataframe(df, use_container_width=True)

            st.subheader("Captured Breach Snapshots")
            cols = st.columns(4)
            for idx, row in df.head(12).iterrows():
                if os.path.exists(row["snapshot_path"]):
                    cols[idx % 4].image(
                        row["snapshot_path"],
                        caption=f"ID: {row['id']} | Conf: {row['confidence']:.2f}\n{row['timestamp']}"
                    )
        else:
            st.info("No breach records stored yet.")
    else:
        st.warning("Database not initialized.")

elif app_mode == "Incident Analytics":
    st.title("📊 Telemetry Metrics & Trends")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM alerts", conn)
        conn.close()

        if not df.empty:
            df["datetime"] = pd.to_datetime(df["timestamp"])
            df["hour"] = df["datetime"].dt.hour

            c1, c2, c3 = st.columns(3)
            c1.metric("Total Breach Events", len(df))
            c2.metric("Mean Detection Confidence", f"{df['confidence'].mean():.2f}")
            c3.metric("Peak Activity Hour", f"{int(df['hour'].mode()[0])}:00 hrs")

            st.markdown("---")
            st.subheader("Hourly Intrusion Frequency")
            st.bar_chart(df["hour"].value_counts().sort_index())
        else:
            st.info("No analytics data available.")