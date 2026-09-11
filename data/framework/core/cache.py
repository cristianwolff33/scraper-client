from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class Cache:
    """
    SQLite-backed cache for visited URLs, downloaded images, and export checkpoints.
    Enables resuming an interrupted run without re-processing completed work.
    """

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.executescript("""
                CREATE TABLE IF NOT EXISTS visited_urls (
                    url TEXT PRIMARY KEY,
                    visited_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS downloaded_images (
                    url TEXT PRIMARY KEY,
                    local_path TEXT,
                    downloaded_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS exported_skus (
                    sku TEXT PRIMARY KEY,
                    format TEXT,
                    exported_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS checkpoints (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TEXT DEFAULT (datetime('now'))
                );
            """)
            self._conn.commit()

    # --- Visited URLs ---

    def mark_visited(self, url: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO visited_urls (url) VALUES (?)", (url,)
            )
            self._conn.commit()

    def is_visited(self, url: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM visited_urls WHERE url = ?", (url,)
            ).fetchone()
        return row is not None

    # --- Downloaded images ---

    def mark_image_downloaded(self, url: str, local_path: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO downloaded_images (url, local_path) VALUES (?, ?)",
                (url, local_path),
            )
            self._conn.commit()

    def is_image_downloaded(self, url: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM downloaded_images WHERE url = ?", (url,)
            ).fetchone()
        return row is not None

    def get_image_path(self, url: str) -> str | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT local_path FROM downloaded_images WHERE url = ?", (url,)
            ).fetchone()
        return row["local_path"] if row else None

    # --- Checkpoints (key-value) ---

    def set_checkpoint(self, key: str, value: Any) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO checkpoints (key, value) VALUES (?, ?)",
                (key, json.dumps(value)),
            )
            self._conn.commit()

    def get_checkpoint(self, key: str, default: Any = None) -> Any:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM checkpoints WHERE key = ?", (key,)
            ).fetchone()
        return json.loads(row["value"]) if row else default

    # --- Exported SKUs ---

    def mark_exported(self, sku: str, fmt: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO exported_skus (sku, format) VALUES (?, ?)",
                (sku, fmt),
            )
            self._conn.commit()

    def is_exported(self, sku: str, fmt: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM exported_skus WHERE sku = ? AND format = ?", (sku, fmt)
            ).fetchone()
        return row is not None

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {
                "visited_urls": self._conn.execute(
                    "SELECT COUNT(*) FROM visited_urls"
                ).fetchone()[0],
                "downloaded_images": self._conn.execute(
                    "SELECT COUNT(*) FROM downloaded_images"
                ).fetchone()[0],
                "exported_skus": self._conn.execute(
                    "SELECT COUNT(*) FROM exported_skus"
                ).fetchone()[0],
            }

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Cache":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()
