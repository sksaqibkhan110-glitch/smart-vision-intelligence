# 🛡️ Smart Vision Intelligence: Edge AI Multi-Zone Threat Detection & Telemetry Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![YOLOv8](https://img.shields.io/badge/YOLOv8-Computer_Vision-00FFFF?style=flat&logo=ultralytics)](https://github.com/ultralytics/ultralytics)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)

An end-to-end edge AI surveillance and incident response system combining real-time computer vision (YOLOv8), multi-zone spatial threat evaluation, automated async audio/Telegram alerting, SQLite audit telemetry, and a Security Operations Center (SOC) dashboard.

---

## 🏛️ System Architecture

```text
[ Live Camera Feed / Video Stream ]
                │
                ▼
┌───────────────────────────────────────────────┐
│           FastAPI Edge Engine (src/api.py)    │
│  ┌─────────────────────────────────────────┐  │
│  │ VisionDetector (YOLOv8n + Zone Check)   │  │
│  └──────────────────┬──────────────────────┘  │
│                     │                         │
│        ┌────────────┴─────────────┐           │
│        ▼                          ▼           │
│  [ SQLite DB ]            [ Threaded Alert ]  │
│  (Audit Telemetry)        ├── Siren Sound     │
│                           └── Telegram Bot    │
└───────────────────────┬───────────────────────┘
                        │ MJPEG Stream & REST Endpoints
                        ▼
┌───────────────────────────────────────────────┐
│     Streamlit SOC Dashboard (app.py)          │
│   • 🔴 Real-Time Vision Feed with Overlay HUD │
│   • 📊 Threat Analytics & Incident Charts     │
│   • 📁 Breach Audit Logs & Forensic Records   │
└───────────────────────────────────────────────┘