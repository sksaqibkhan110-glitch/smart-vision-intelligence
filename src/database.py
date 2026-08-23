import sqlite3
import datetime
from collections import Counter

class AlertDatabase:
    def __init__(self, db_path="data/telemetry.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS security_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    threat_type TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    snapshot_path TEXT
                )
            """)
            conn.commit()

    def log_alert(self, threat_type: str, confidence: float, snapshot_path: str = None):
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO security_logs (timestamp, threat_type, confidence, snapshot_path)
                VALUES (?, ?, ?, ?)
            """, (ts, threat_type, confidence, snapshot_path))
            conn.commit()

    def fetch_recent_alerts(self, limit: int = 15):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, threat_type, confidence, snapshot_path 
                FROM security_logs 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return cursor.fetchall()

    def get_threat_analytics(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT threat_type FROM security_logs")
            rows = cursor.fetchall()
            counts = Counter([r[0] for r in rows])
            return dict(counts)