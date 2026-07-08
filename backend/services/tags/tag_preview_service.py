"""TagPreviewService - dry-run / diff for batch tag operations.

Reads the current on-disk tags via AudioTagger for each file, applies the
proposed changes in memory, and returns a structured diff without writing."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import msgspec

from api.v1.schemas.tags import (
    BatchTagPreviewItem,
    TagDiffEntry,
    TrackTagEntry,
)

if TYPE_CHECKING:
    from infrastructure.audio.tagger import AudioTagger
    from infrastructure.persistence.library_db import LibraryDB
    from models.audio import AudioTag

logger = logging.getLogger(__name__)


class TagPreviewService:
    """Reads current tags, computes diff, never writes."""

    def __init__(self, tagger: AudioTagger, library_db: LibraryDB):
        self._tagger = tagger
        self._db = library_db

    async def preview_batch(
        self, entries: list[TrackTagEntry]
    ) -> list[BatchTagPreviewItem]:
        results: list[BatchTagPreviewItem] = []
        for entry in entries:
            try:
                row = await self._db.get_library_file_by_id(entry.file_id)
                if not row:
                    continue
                file_path = Path(row["file_path"])
                current_tag, _info = self._tagger.read_tags(file_path)
                proposed = self._apply_entries(current_tag, entry)
                diffs = self._compute_diff(current_tag, proposed, entry)
                results.append(
                    BatchTagPreviewItem(
                        file_id=entry.file_id,
                        file_path=str(file_path),
                        title=current_tag.title,
                        diffs=diffs,
                    )
                )
            except Exception:
                logger.warning(
                    "Preview failed for file %s", entry.file_id, exc_info=True
                )
        return results

    def _apply_entries(self, tag: AudioTag, entry: TrackTagEntry) -> AudioTag:
        from models.audio import AudioTag

        current = msgspec.structs.asdict(tag)
        for field in ("title", "artist", "album", "album_artist", "year", "genre"):
            val = getattr(entry, field, None)
            if val is not None:
                current[field] = val
        if entry.track_number is not None:
            current["track_number"] = entry.track_number
        if entry.disc_number is not None:
            current["disc_number"] = entry.disc_number
        return AudioTag(**current)

    def _compute_diff(
        self, old: AudioTag, new: AudioTag, entry: TrackTagEntry
    ) -> list[TagDiffEntry]:
        diffs: list[TagDiffEntry] = []
        candidates = [
            ("title", "title"),
            ("artist", "artist"),
            ("album", "album"),
            ("album_artist", "album_artist"),
            ("year", "year"),
            ("genre", "genre"),
            ("track_number", "track_number"),
            ("disc_number", "disc_number"),
        ]
        for schema_field, tag_field in candidates:
            if getattr(entry, schema_field, None) is not None:
                old_val = getattr(old, tag_field, None)
                new_val = getattr(new, tag_field, None)
                if old_val != new_val:
                    diffs.append(
                        TagDiffEntry(
                            field=tag_field,
                            old_value=str(old_val) if old_val is not None else None,
                            new_value=str(new_val) if new_val is not None else None,
                        )
                    )
        return diffs
