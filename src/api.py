import sqlite3
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Vision Intelligence Security API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "data/surveillance.db"

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "active", "service": "vision-telemetry-engine"}

@app.get("/api/v1/alerts")
def fetch_alerts(limit: int = 10):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    records = cursor.fetchall()
    conn.close()
    return {"count": len(records), "data": [dict(row) for row in records]}

@app.get("/api/v1/analytics/summary")
def fetch_summary():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM alerts", conn)
    conn.close()

    if df.empty:
        return {"total_incidents": 0, "peak_hour": None, "avg_confidence": 0.0}

    df["datetime"] = pd.to_datetime(df["timestamp"])
    peak_hour = int(df["datetime"].dt.hour.mode()[0])
    avg_conf = float(df["confidence"].mean())

    return {
        "total_incidents": len(df),
        "peak_hour": peak_hour,
        "avg_confidence": round(avg_conf, 2),
        "unique_objects": df["object_name"].unique().tolist()
    }