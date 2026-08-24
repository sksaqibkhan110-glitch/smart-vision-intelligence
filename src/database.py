import sqlite3
import os
from datetime import datetime

class AlertDatabase:
    def __init__(self, db_path="data/alerts.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    threat_type TEXT,
                    confidence REAL,
                    snapshot_path TEXT
                )
            """)
            conn.commit()

    def log_alert(self, threat_type, confidence, snapshot_path):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO alerts (timestamp, threat_type, confidence, snapshot_path) VALUES (?, ?, ?, ?)",
                (now, threat_type, float(confidence), snapshot_path)
            )
            conn.commit()

    def fetch_recent_alerts(self, limit=15):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT id, timestamp, threat_type, confidence, snapshot_path FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def fetch_analytics_summary(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM alerts")
            total = cursor.fetchone()[0] or 0

            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp LIKE ?", (f"{today}%",))
            today_count = cursor.fetchone()[0] or 0

            cursor.execute("SELECT timestamp FROM alerts ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            last_ts = row[0] if row else "N/A"

            cursor.execute("SELECT threat_type, COUNT(*) FROM alerts GROUP BY threat_type")
            breakdown = {threat: count for threat, count in cursor.fetchall()}

            return {
                "total_alerts": total,
                "threats_today": today_count,
                "last_alert_time": last_ts,
                "threat_breakdown": breakdown
            }