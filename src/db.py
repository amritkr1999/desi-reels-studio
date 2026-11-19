"""SQLite database manager for DesiReels Studio."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import config

# Indian Standard Time (UTC+5:30) helper
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> str:
    """Return current timestamp as ISO 8601 string in IST."""
    return datetime.now(IST).isoformat()


class Database:
    """Thread-safe SQLite connection and query helper."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        self.db_path = db_path or config.DATABASE_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_schema(self) -> None:
        """Create database tables if they do not exist."""
        with self.get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS topics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL UNIQUE,
                    region TEXT NOT NULL,
                    category TEXT NOT NULL,
                    ground_truth_summary TEXT,
                    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'scripted', 'produced', 'published', 'rejected')),
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic_id INTEGER NOT NULL REFERENCES topics(id),
                    title TEXT NOT NULL,
                    duration_seconds REAL NOT NULL,
                    script_text TEXT NOT NULL,
                    audio_path TEXT,
                    video_path TEXT,
                    render_time_seconds REAL,
                    status TEXT DEFAULT 'rendered' CHECK(status IN ('rendered', 'approved', 'rejected')),
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS publishing_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER NOT NULL REFERENCES videos(id),
                    platform TEXT NOT NULL CHECK(platform IN ('youtube', 'instagram', 'facebook')),
                    scheduled_for_ist TEXT NOT NULL,
                    published_at_ist TEXT,
                    external_post_id TEXT,
                    external_post_url TEXT,
                    status TEXT DEFAULT 'staged' CHECK(status IN ('staged', 'dry_run', 'published', 'failed')),
                    error_message TEXT
                );

                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    publishing_log_id INTEGER REFERENCES publishing_log(id),
                    video_id INTEGER REFERENCES videos(id),
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    retention_rate REAL DEFAULT 0.0,
                    logged_at_ist TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS feedback_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id INTEGER REFERENCES videos(id),
                    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
                    critique TEXT NOT NULL,
                    applied_playbook_changes TEXT,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_topics_status ON topics(status);
                CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
                CREATE INDEX IF NOT EXISTS idx_publishing_status ON publishing_log(status);
                """
            )

    # --------------------------------------------------------------------------
    # Topics Operations
    # --------------------------------------------------------------------------
    def insert_topic(
        self,
        title: str,
        region: str,
        category: str,
        ground_truth_summary: Optional[str] = None,
    ) -> Optional[int]:
        """Insert a topic, ignoring if title already exists."""
        ts = now_ist()
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO topics (title, region, category, ground_truth_summary, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?)
                """,
                (title, region, category, ground_truth_summary, ts, ts),
            )
            return cur.lastrowid if cur.rowcount > 0 else None

    def get_next_pending_topic(self) -> Optional[Dict[str, Any]]:
        """Retrieve the oldest pending topic."""
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM topics WHERE status = 'pending' ORDER BY id ASC LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    def update_topic_status(
        self, topic_id: int, status: str, ground_truth: Optional[str] = None
    ) -> None:
        """Update a topic's status and ground truth summary."""
        ts = now_ist()
        with self.get_connection() as conn:
            if ground_truth:
                conn.execute(
                    """
                    UPDATE topics SET status = ?, ground_truth_summary = ?, updated_at = ? WHERE id = ?
                    """,
                    (status, ground_truth, ts, topic_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE topics SET status = ?, updated_at = ? WHERE id = ?
                    """,
                    (status, ts, topic_id),
                )

    def list_topics(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List topics for the dashboard."""
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM topics ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # --------------------------------------------------------------------------
    # Video Operations
    # --------------------------------------------------------------------------
    def insert_video(
        self,
        topic_id: int,
        title: str,
        duration_seconds: float,
        script_text: str,
        audio_path: str,
        video_path: str,
        render_time_seconds: float,
    ) -> int:
        ts = now_ist()
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO videos (topic_id, title, duration_seconds, script_text, audio_path, video_path, render_time_seconds, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'rendered', ?)
                """,
                (
                    topic_id,
                    title,
                    duration_seconds,
                    script_text,
                    audio_path,
                    video_path,
                    render_time_seconds,
                    ts,
                ),
            )
            return cur.lastrowid

    def get_latest_video(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute(
                """
                SELECT v.*, t.title as topic_title, t.region, t.category 
                FROM videos v 
                JOIN topics t ON v.topic_id = t.id 
                ORDER BY v.id DESC LIMIT 1
                """
            ).fetchone()
            return dict(row) if row else None

    def update_video_status(self, video_id: int, status: str) -> None:
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE videos SET status = ? WHERE id = ?", (status, video_id)
            )

    # --------------------------------------------------------------------------
    # Publishing & Performance Operations
    # --------------------------------------------------------------------------
    def log_publish_event(
        self,
        video_id: int,
        platform: str,
        scheduled_for_ist: str,
        status: str = "staged",
        published_at_ist: Optional[str] = None,
        external_post_id: Optional[str] = None,
        external_post_url: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> int:
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO publishing_log (video_id, platform, scheduled_for_ist, published_at_ist, external_post_id, external_post_url, status, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    video_id,
                    platform,
                    scheduled_for_ist,
                    published_at_ist,
                    external_post_id,
                    external_post_url,
                    status,
                    error_message,
                ),
            )
            return cur.lastrowid

    def log_feedback(
        self,
        video_id: Optional[int],
        rating: int,
        critique: str,
        applied_playbook_changes: Optional[Dict[str, Any]] = None,
    ) -> int:
        ts = now_ist()
        changes_json = (
            json.dumps(applied_playbook_changes) if applied_playbook_changes else None
        )
        with self.get_connection() as conn:
            cur = conn.execute(
                """
                INSERT INTO feedback_log (video_id, rating, critique, applied_playbook_changes, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (video_id, rating, critique, changes_json, ts),
            )
            return cur.lastrowid

    def get_publishing_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT p.*, v.title as video_title 
                FROM publishing_log p
                JOIN videos v ON p.video_id = v.id
                ORDER BY p.id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]


db = Database()
