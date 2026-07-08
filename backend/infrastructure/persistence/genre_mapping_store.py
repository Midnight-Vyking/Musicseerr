"""Genre mapping persistence — raw → canonical genre mappings with stats.

Owns tables: ``genre_mappings``, ``genre_stats``.
Shares the same SQLite database as LibraryDB and GenreIndex.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from infrastructure.persistence._database import PersistenceBase

logger = logging.getLogger(__name__)


class GenreMappingStore(PersistenceBase):
    """Owns tables: ``genre_mappings``, ``genre_stats``."""

    def _ensure_tables(self) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """\
                CREATE TABLE IF NOT EXISTS genre_mappings (
                    raw_genre TEXT PRIMARY KEY,
                    canonical_genre TEXT NOT NULL,
                    confidence REAL DEFAULT 1.0,
                    created_at INTEGER NOT NULL DEFAULT (unixepoch()),
                    updated_at INTEGER NOT NULL DEFAULT (unixepoch())
                )
                """
            )
            conn.execute(
                """\
                CREATE TABLE IF NOT EXISTS genre_stats (
                    canonical_genre TEXT PRIMARY KEY,
                    track_count INTEGER NOT NULL DEFAULT 0,
                    file_format TEXT DEFAULT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    async def get_mapping(self, raw_genre: str) -> dict[str, Any] | None:
        """Return {raw_genre, canonical_genre, confidence} or None."""

        def operation(conn: sqlite3.Connection) -> dict[str, Any] | None:
            row = conn.execute(
                "SELECT raw_genre, canonical_genre, confidence FROM genre_mappings WHERE raw_genre = ?",
                (raw_genre,),
            ).fetchone()
            if row is None:
                return None
            return {
                "raw_genre": row["raw_genre"],
                "canonical_genre": row["canonical_genre"],
                "confidence": row["confidence"],
            }

        return await self._read(operation)

    async def set_mapping(
        self, raw_genre: str, canonical_genre: str, confidence: float = 1.0
    ) -> None:
        """Insert or update a raw → canonical mapping."""

        def operation(conn: sqlite3.Connection) -> None:
            conn.execute(
                """\
                INSERT INTO genre_mappings (raw_genre, canonical_genre, confidence, updated_at)
                VALUES (?, ?, ?, unixepoch())
                ON CONFLICT(raw_genre) DO UPDATE SET
                    canonical_genre = excluded.canonical_genre,
                    confidence = excluded.confidence,
                    updated_at = unixepoch()
                """,
                (raw_genre, canonical_genre, confidence),
            )

        await self._write(operation)

    async def delete_mapping(self, raw_genre: str) -> bool:
        """Remove a mapping. Returns True if one was deleted."""

        def operation(conn: sqlite3.Connection) -> bool:
            cursor = conn.execute(
                "DELETE FROM genre_mappings WHERE raw_genre = ?", (raw_genre,)
            )
            return cursor.rowcount > 0

        return await self._write(operation)

    async def get_all_mappings(self) -> list[dict[str, Any]]:
        """Return all mappings."""

        def operation(conn: sqlite3.Connection) -> list[dict[str, Any]]:
            rows = conn.execute(
                "SELECT raw_genre, canonical_genre, confidence FROM genre_mappings ORDER BY raw_genre"
            ).fetchall()
            return [
                {
                    "raw_genre": row["raw_genre"],
                    "canonical_genre": row["canonical_genre"],
                    "confidence": row["confidence"],
                }
                for row in rows
            ]

        return await self._read(operation)

    async def get_unmapped_genres(
        self, library_genres: list[str]
    ) -> list[str]:
        """Return raw genres from the library that have NO mapping."""

        if not library_genres:
            return []

        def operation(conn: sqlite3.Connection) -> list[str]:
            placeholders = ",".join("?" * len(library_genres))
            mapped_rows = conn.execute(
                f"SELECT raw_genre FROM genre_mappings WHERE raw_genre IN ({placeholders})",
                library_genres,
            ).fetchall()
            mapped_set = {row["raw_genre"] for row in mapped_rows}
            return [g for g in library_genres if g not in mapped_set]

        return await self._read(operation)

    async def upsert_genre_stats(
        self, canonical_genre: str, track_count: int
    ) -> None:
        """Update (or insert) the track count for a canonical genre."""

        def operation(conn: sqlite3.Connection) -> None:
            conn.execute(
                """\
                INSERT INTO genre_stats (canonical_genre, track_count)
                VALUES (?, ?)
                ON CONFLICT(canonical_genre) DO UPDATE SET
                    track_count = excluded.track_count
                """,
                (canonical_genre, track_count),
            )

        await self._write(operation)

    async def get_genre_stats(
        self, canonical_genre: str | None = None
    ) -> list[dict[str, Any]]:
        """Return genre stats. If canonical_genre is given, filter to that one."""

        def operation(conn: sqlite3.Connection) -> list[dict[str, Any]]:
            if canonical_genre:
                rows = conn.execute(
                    "SELECT canonical_genre, track_count FROM genre_stats WHERE canonical_genre = ? ORDER BY track_count DESC",
                    (canonical_genre,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT canonical_genre, track_count FROM genre_stats ORDER BY track_count DESC"
                ).fetchall()
            return [
                {
                    "canonical_genre": row["canonical_genre"],
                    "track_count": row["track_count"],
                }
                for row in rows
            ]

        return await self._read(operation)

    async def scan_library_genres(self) -> list[str]:
        """Scan library_files table for unique non-empty genres."""

        def operation(conn: sqlite3.Connection) -> list[str]:
            rows = conn.execute(
                "SELECT DISTINCT genre FROM library_files WHERE genre IS NOT NULL AND genre != '' AND deleted_at IS NULL ORDER BY genre COLLATE NOCASE"
            ).fetchall()
            return [row["genre"] for row in rows]

        return await self._read(operation)

    async def bulk_set_mappings(
        self, entries: list[tuple[str, str, float]]
    ) -> int:
        """Set many mappings at once. Each entry is (raw_genre, canonical_genre, confidence).
        Returns count of inserted/updated rows."""

        def operation(conn: sqlite3.Connection) -> int:
            count = 0
            for raw_genre, canonical_genre, confidence in entries:
                conn.execute(
                    """\
                    INSERT INTO genre_mappings (raw_genre, canonical_genre, confidence, updated_at)
                    VALUES (?, ?, ?, unixepoch())
                    ON CONFLICT(raw_genre) DO UPDATE SET
                        canonical_genre = excluded.canonical_genre,
                        confidence = excluded.confidence,
                        updated_at = unixepoch()
                    """,
                    (raw_genre, canonical_genre, confidence),
                )
                count += 1
            return count

        return await self._write(operation)
