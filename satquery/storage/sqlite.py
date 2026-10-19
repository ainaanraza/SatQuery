import json
import sqlite3
import threading
from datetime import datetime, timezone

from .base import StorageBackend

_SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    analysis_id TEXT PRIMARY KEY,
    status      TEXT NOT NULL,
    request     TEXT,
    result      TEXT,
    error       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
)
"""
_FIELDS = ("status", "request", "result", "error")


class SQLiteBackend(StorageBackend):
    """Analysis records in SQLite. Thread-safe; `request` and `result` are stored as JSON text."""

    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self._lock = threading.Lock()
        # One shared connection, serialized by the lock (also keeps ":memory:" databases alive).
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock, self._conn:
            self._conn.execute(_SCHEMA)

    def save_analysis(self, analysis_id, data):
        """Insert or update a record; only the fields present in `data` are changed."""
        now = datetime.now(timezone.utc).isoformat()
        values = {k: data[k] for k in _FIELDS if k in data}
        for key in ("request", "result"):
            if key in values and values[key] is not None:
                values[key] = json.dumps(values[key])
        with self._lock, self._conn:
            exists = self._conn.execute(
                "SELECT 1 FROM analyses WHERE analysis_id = ?", (analysis_id,)
            ).fetchone()
            if exists:
                assignments = ", ".join(f"{k} = ?" for k in values)
                self._conn.execute(
                    f"UPDATE analyses SET {assignments}{', ' if values else ''}updated_at = ? WHERE analysis_id = ?",
                    (*values.values(), now, analysis_id),
                )
            else:
                values.setdefault("status", "queued")
                columns = ", ".join(values)
                placeholders = ", ".join("?" for _ in values)
                self._conn.execute(
                    f"INSERT INTO analyses (analysis_id, {columns}, created_at, updated_at) VALUES (?, {placeholders}, ?, ?)",
                    (analysis_id, *values.values(), now, now),
                )

    def get_analysis(self, analysis_id):
        with self._lock:
            row = self._conn.execute("SELECT * FROM analyses WHERE analysis_id = ?", (analysis_id,)).fetchone()
        return self._row_to_dict(row) if row else None

    def list_analyses(self, limit=20, statuses=None):
        query = "SELECT * FROM analyses"
        params = []
        if statuses:
            query += f" WHERE status IN ({', '.join('?' for _ in statuses)})"
            params.extend(statuses)
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._lock:
            rows = self._conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def close(self):
        with self._lock:
            self._conn.close()

    @staticmethod
    def _row_to_dict(row):
        record = dict(row)
        for key in ("request", "result"):
            if record.get(key) is not None:
                record[key] = json.loads(record[key])
        return record
