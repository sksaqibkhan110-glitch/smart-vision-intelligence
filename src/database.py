import sqlite3
import datetime
import os

class AlertDatabase:
    def __init__(self, db_path="data/surveillance.db"):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            object_name TEXT,
            confidence REAL,
            snapshot_path TEXT
        );
        """
        with self.conn:
            self.conn.execute(query)

    def log_alert(self, object_name: str, confidence: float, snapshot_path: str):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        query = """
        INSERT INTO alerts (timestamp, object_name, confidence, snapshot_path)
        VALUES (?, ?, ?, ?)
        """
        with self.conn:
            self.conn.execute(query, (timestamp, object_name, round(confidence, 2), snapshot_path))
            