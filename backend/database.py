"""
SQLite database for flight price alerts.
The DB file (alerts.db) is created automatically on first run.
"""

import sqlite3
import json
import os
from datetime import datetime

# Railway persistent volume mounts at /data by default.
# Locally falls back to the project directory.
_data_dir = os.getenv("RAILWAY_VOLUME_MOUNT_PATH", os.path.dirname(__file__))
DB_PATH = os.path.join(_data_dir, "alerts.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id          TEXT PRIMARY KEY,
                email       TEXT NOT NULL,
                origin      TEXT NOT NULL,
                destination TEXT NOT NULL,
                filters     TEXT NOT NULL,   -- JSON blob of all search params
                last_offers TEXT,            -- JSON blob of last seen offer ids+prices
                created_at  TEXT NOT NULL,
                last_run_at TEXT
            )
        """)
        conn.commit()


def create_alert(alert_id: str, email: str, origin: str, destination: str, filters: dict):
    with get_conn() as conn:
        conn.execute(
            """INSERT INTO alerts (id, email, origin, destination, filters, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (alert_id, email, origin.upper(), destination.upper(),
             json.dumps(filters), datetime.utcnow().isoformat())
        )
        conn.commit()


def get_all_alerts():
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM alerts").fetchall()
    return [dict(r) for r in rows]


def get_alerts_for_email(email: str):
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE email = ? ORDER BY created_at DESC", (email,)
        ).fetchall()
    return [dict(r) for r in rows]


def delete_alert(alert_id: str):
    with get_conn() as conn:
        conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()


def update_alert_run(alert_id: str, last_offers: list):
    with get_conn() as conn:
        conn.execute(
            "UPDATE alerts SET last_run_at = ?, last_offers = ? WHERE id = ?",
            (datetime.utcnow().isoformat(), json.dumps(last_offers), alert_id)
        )
        conn.commit()
