"""Tests for TagPreviewService - dry-run diff computation for batch tag operations."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from api.v1.schemas.tags import TrackTagEntry
from models.audio import AudioTag
from services.tags.tag_preview_service import TagPreviewService


@pytest.fixture
def mock_tagger():
    """AudioTagger that returns a known AudioTag from read_tags."""
    tagger = MagicMock()
    tagger.read_tags.return_value = (
        AudioTag(
            title="Bohemian Rhapsody",
            artist="Queen",
            album="A Night at the Opera",
            track_number=11,
            album_artist="Queen",
            disc_number=1,
            year=1975,
            genre="Rock",
        ),
        MagicMock(),  # AudioInfo - unused by preview
    )
    return tagger


@pytest.fixture
def mock_db():
    """LibraryDB that returns a known row from get_library_file_by_id."""
    db = MagicMock()
    db.get_library_file_by_id = AsyncMock(
        return_value={
            "file_path": "/music/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3",
        }
    )
    return db


@pytest.fixture
def service(mock_tagger, mock_db):
    return TagPreviewService(tagger=mock_tagger, library_db=mock_db)


class TestPreviewBatch:
    @pytest.mark.asyncio
    async def test_no_changes_empty_diffs(self, service, mock_db):
        """When no fields diverge from current tags, diffs should be empty."""
        entries = [
            TrackTagEntry(
                file_id="abc-123",
                title="Bohemian Rhapsody",
                artist="Queen",
                album="A Night at the Opera",
                track_number=11,
                album_artist="Queen",
                disc_number=1,
                year=1975,
                genre="Rock",
            )
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 1
        assert results[0].diffs == []

    @pytest.mark.asyncio
    async def test_changing_genre_diff(self, service, mock_db):
        """Changing only the genre gives one diff entry with old/new values."""
        entries = [
            TrackTagEntry(file_id="abc-123", genre="Classic Rock")
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 1
        assert len(results[0].diffs) == 1
        diff = results[0].diffs[0]
        assert diff.field == "genre"
        assert diff.old_value == "Rock"
        assert diff.new_value == "Classic Rock"

    @pytest.mark.asyncio
    async def test_changing_multiple_fields(self, service, mock_db):
        """Changing title and artist produces two diffs."""
        entries = [
            TrackTagEntry(
                file_id="abc-123",
                title="Killer Queen",
                artist="QUEEN",
            )
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 1
        assert len(results[0].diffs) == 2
        diffs_by_field = {d.field: d for d in results[0].diffs}
        assert diffs_by_field["title"].old_value == "Bohemian Rhapsody"
        assert diffs_by_field["title"].new_value == "Killer Queen"
        assert diffs_by_field["artist"].old_value == "Queen"
        assert diffs_by_field["artist"].new_value == "QUEEN"

    @pytest.mark.asyncio
    async def test_nonexistent_file_skipped(self, service, mock_db):
        """A file_id not in the DB is silently skipped."""
        mock_db.get_library_file_by_id.return_value = None
        entries = [
            TrackTagEntry(file_id="no-such-file", genre="Jazz")
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_tagger_read_error_skipped(self, service, mock_tagger):
        """If AudioTagger raises, the entry is silently skipped."""
        mock_tagger.read_tags.side_effect = ValueError("bad file")
        entries = [
            TrackTagEntry(file_id="abc-123", genre="Jazz")
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_batch_mixed_results(self, service, mock_db):
        """Valid entries return results; invalid ones are skipped."""
        async def get_file(file_id):
            if file_id == "valid-1":
                return {"file_path": "/music/track1.mp3"}
            return None

        mock_db.get_library_file_by_id = get_file
        entries = [
            TrackTagEntry(file_id="valid-1", genre="Pop"),
            TrackTagEntry(file_id="invalid-1", genre="Jazz"),
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 1
        assert results[0].file_id == "valid-1"

    @pytest.mark.asyncio
    async def test_preview_item_has_correct_shape(self, service, mock_db):
        """Verify the preview item contains all expected fields."""
        entries = [
            TrackTagEntry(file_id="abc-123", genre="Classic Rock")
        ]
        results = await service.preview_batch(entries)
        item = results[0]
        assert item.file_id == "abc-123"
        assert item.file_path == "/music/Queen/A Night at the Opera/11 - Bohemian Rhapsody.mp3"
        assert item.title == "Bohemian Rhapsody"
        assert len(item.diffs) == 1

    @pytest.mark.asyncio
    async def test_only_requested_fields_in_diffs(self, service, mock_db):
        """Diffs should only contain fields the user explicitly provided."""
        entries = [
            TrackTagEntry(
                file_id="abc-123",
                title="Bohemian Rhapsody",
                artist="Queen",
                album="A Night at the Opera",
            )
        ]
        results = await service.preview_batch(entries)
        assert len(results) == 1
        assert results[0].diffs == []
