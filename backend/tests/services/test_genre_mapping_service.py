"""Tests for GenreMappingStore and GenreMappingService."""

from __future__ import annotations

import tempfile
import threading
from pathlib import Path

import pytest
import yaml

from infrastructure.persistence.genre_mapping_store import GenreMappingStore
from services.tags.genre_taxonomy_service import GenreTaxonomyService
from services.tags.genre_mapping_service import GenreMappingService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def taxonomy_yaml() -> str:
    """Minimal taxonomy for testing."""
    data = {
        "categories": [
            {
                "name": "Rock",
                "genres": [
                    "Alternative Rock",
                    "Classic Rock",
                    "Hard Rock",
                    "Indie Rock",
                    "Progressive Rock",
                    "Psychedelic Rock",
                ],
            },
            {
                "name": "Electronic",
                "genres": [
                    "Ambient",
                    "House",
                    "Techno",
                    "Trance",
                ],
            },
        ]
    }
    return yaml.safe_dump(data)


@pytest.fixture
def taxonomy_path(taxonomy_yaml: str) -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(taxonomy_yaml)
        return f.name


@pytest.fixture
def taxonomy_svc(taxonomy_path: str) -> GenreTaxonomyService:
    return GenreTaxonomyService(taxonomy_path=Path(taxonomy_path))


@pytest.fixture
def db_path() -> str:
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        return f.name


@pytest.fixture
def store(db_path: str) -> GenreMappingStore:
    lock = threading.Lock()
    return GenreMappingStore(db_path=Path(db_path), write_lock=lock)


@pytest.fixture
def mapping_svc(taxonomy_svc: GenreTaxonomyService, store: GenreMappingStore) -> GenreMappingService:
    return GenreMappingService(taxonomy=taxonomy_svc, store=store)


# ---------------------------------------------------------------------------
# GenreMappingStore tests
# ---------------------------------------------------------------------------


class TestGenreMappingStore:
    """Tests for GenreMappingStore (persistence layer)."""

    @pytest.mark.asyncio
    async def test_set_and_get_mapping(self, store: GenreMappingStore):
        await store.set_mapping("raw rock", "Classic Rock", 0.95)
        result = await store.get_mapping("raw rock")
        assert result is not None
        assert result["raw_genre"] == "raw rock"
        assert result["canonical_genre"] == "Classic Rock"
        assert result["confidence"] == 0.95

    @pytest.mark.asyncio
    async def test_get_nonexistent_mapping(self, store: GenreMappingStore):
        result = await store.get_mapping("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_update_mapping(self, store: GenreMappingStore):
        await store.set_mapping("raw rock", "Classic Rock", 1.0)
        # Update
        await store.set_mapping("raw rock", "Hard Rock", 0.8)
        result = await store.get_mapping("raw rock")
        assert result["canonical_genre"] == "Hard Rock"
        assert result["confidence"] == 0.8

    @pytest.mark.asyncio
    async def test_delete_mapping(self, store: GenreMappingStore):
        await store.set_mapping("raw rock", "Classic Rock", 1.0)
        deleted = await store.delete_mapping("raw rock")
        assert deleted is True
        assert await store.get_mapping("raw rock") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, store: GenreMappingStore):
        deleted = await store.delete_mapping("nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_get_all_mappings(self, store: GenreMappingStore):
        await store.set_mapping("raw1", "Techno", 1.0)
        await store.set_mapping("raw2", "House", 0.9)
        mappings = await store.get_all_mappings()
        assert len(mappings) == 2
        raw_genres = {m["raw_genre"] for m in mappings}
        assert raw_genres == {"raw1", "raw2"}

    @pytest.mark.asyncio
    async def test_get_unmapped_genres(self, store: GenreMappingStore):
        await store.set_mapping("raw1", "Techno", 1.0)
        library = ["raw1", "raw2", "raw3"]
        unmapped = await store.get_unmapped_genres(library)
        assert unmapped == ["raw2", "raw3"]

    @pytest.mark.asyncio
    async def test_get_unmapped_genres_empty(self, store: GenreMappingStore):
        unmapped = await store.get_unmapped_genres([])
        assert unmapped == []

    @pytest.mark.asyncio
    async def test_genre_stats(self, store: GenreMappingStore):
        await store.upsert_genre_stats("Techno", 42)
        await store.upsert_genre_stats("House", 17)
        stats = await store.get_genre_stats()
        assert len(stats) == 2
        assert stats[0]["track_count"] == 42  # Techno first (DESC)

    @pytest.mark.asyncio
    async def test_genre_stats_filtered(self, store: GenreMappingStore):
        await store.upsert_genre_stats("Techno", 42)
        stats = await store.get_genre_stats(canonical_genre="Techno")
        assert len(stats) == 1
        assert stats[0]["canonical_genre"] == "Techno"

    @pytest.mark.asyncio
    async def test_bulk_set_mappings(self, store: GenreMappingStore):
        entries = [
            ("raw1", "Techno", 1.0),
            ("raw2", "House", 0.9),
            ("raw3", "Trance", 0.85),
        ]
        count = await store.bulk_set_mappings(entries)
        assert count == 3
        mappings = await store.get_all_mappings()
        assert len(mappings) == 3


# ---------------------------------------------------------------------------
# GenreMappingService tests
# ---------------------------------------------------------------------------


class TestGenreMappingService:
    """Tests for GenreMappingService (business logic)."""

    @pytest.mark.asyncio
    async def test_set_and_get_mapping(self, mapping_svc: GenreMappingService):
        await mapping_svc.set_mapping("rock stuff", "Classic Rock", 1.0)
        result = await mapping_svc.get_mapping("rock stuff")
        assert result is not None
        assert result["canonical_genre"] == "Classic Rock"

    @pytest.mark.asyncio
    async def test_auto_map_exact(self, mapping_svc: GenreMappingService):
        result = await mapping_svc.auto_map("Techno")
        assert result is not None
        assert result["suggestion"] == "Techno"
        assert result["confidence"] == 1.0

    @pytest.mark.asyncio
    async def test_auto_map_fuzzy(self, mapping_svc: GenreMappingService):
        result = await mapping_svc.auto_map("classic rok")
        assert result is not None
        suggestion = result["suggestion"]
        assert "Classic Rock" in suggestion or "Rock" in suggestion

    @pytest.mark.asyncio
    async def test_auto_map_no_match(self, mapping_svc: GenreMappingService):
        result = await mapping_svc.auto_map("xyzzzy_not_a_genre")
        assert result is None

    @pytest.mark.asyncio
    async def test_auto_map_all(self, mapping_svc: GenreMappingService):
        results = await mapping_svc.auto_map_all(["Techno", "xyzzzy"])
        techno_result = results["Techno"]
        assert techno_result is not None
        assert techno_result["suggestion"] == "Techno"
        assert results["xyzzzy"] is None

    @pytest.mark.asyncio
    async def test_get_unmapped_genres(self, mapping_svc: GenreMappingService):
        await mapping_svc.set_mapping("Techno", "Techno")
        unmapped = await mapping_svc.get_unmapped_genres(["Techno", "House", "Unknown"])
        assert unmapped == ["House", "Unknown"]

    @pytest.mark.asyncio
    async def test_get_all_mappings(self, mapping_svc: GenreMappingService):
        await mapping_svc.set_mapping("raw1", "Techno", 1.0)
        await mapping_svc.set_mapping("raw2", "House", 0.9)
        mappings = await mapping_svc.get_all_mappings()
        assert len(mappings) == 2

    @pytest.mark.asyncio
    async def test_genre_stats(self, mapping_svc: GenreMappingService):
        # Directly use store for stats since mapping_svc doesn't write stats
        stats = await mapping_svc.get_genre_stats()
        assert isinstance(stats, list)
