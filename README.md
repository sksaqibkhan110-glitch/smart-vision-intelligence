# Smart Vision Intelligence

A real-time security surveillance and computer vision application that detects zone intrusions, saves incident snapshots, and provides an analytics dashboard.

Built using YOLOv8, OpenCV, FastAPI, and Streamlit.

---

## Features

* **Restricted Zone Detection:** Highlights a security polygon on the live camera stream and detects when a person crosses into the boundary.
* **Incident Logging & Snapshots:** Saves breach images automatically to disk with a 3-second cooldown buffer and logs metadata into a SQLite database.
* **REST API:** FastAPI backend to fetch logged breaches and summary analytics via JSON endpoints.
* **Interactive Dashboard:** Streamlit UI to monitor live incident metrics, hourly trends, and captured evidence snapshots.
* **Video File Testing:** Allows running detection on pre-recorded CCTV clips directly from the interface.

---

## Project Structure

```text
smart-vision-intelligence/
├── data/
│   ├── alerts/            # Saved breach snapshots
│   └── surveillance.db    # SQLite database
├── src/
│   ├── api.py             # FastAPI backend endpoints
│   ├── database.py        # SQLite connection and queries
│   ├── detector.py        # Core YOLOv8 live stream processor
│   └── stream_processor.py# Video file processing module
├── app.py                 # Streamlit telemetry dashboard
├── main.py                # Live camera entry point
├── Dockerfile             # Container configuration
├── docker-compose.yml     # Multi-service setup
└── requirements.txt       # Project dependencies