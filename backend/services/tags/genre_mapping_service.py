"""GenreMappingService - manage raw → canonical genre mappings.

Uses GenreTaxonomyService for fuzzy matching suggestions and
GenreMappingStore for persistence.
"""

from __future__ import annotations

import logging

from services.tags.genre_taxonomy_service import GenreTaxonomyService
from infrastructure.persistence.genre_mapping_store import GenreMappingStore

logger = logging.getLogger(__name__)


class GenreMappingService:
    """Exposes genre mapping operations: get/set, auto-map, scan, stats."""

    def __init__(
        self,
        taxonomy: GenreTaxonomyService,
        store: GenreMappingStore,
    ) -> None:
        self._taxonomy = taxonomy
        self._store = store

    async def get_mapping(self, raw_genre: str) -> dict | None:
        """Get the canonical mapping for a raw genre, or None if unmapped."""
        return await self._store.get_mapping(raw_genre)

    async def set_mapping(
        self, raw_genre: str, canonical_genre: str, confidence: float = 1.0
    ) -> None:
        """Set (or overwrite) a raw → canonical mapping."""
        await self._store.set_mapping(raw_genre, canonical_genre, confidence)

    async def auto_map(self, raw_genre: str, threshold: int = 80) -> dict | None:
        """Get the best fuzzy-match suggestion for a raw genre.
        Returns {suggestion, confidence} or None if no match above threshold."""
        matches = self._taxonomy.fuzzy_match(raw_genre, threshold=threshold)
        if not matches:
            return None
        best_name, best_score = matches[0]
        return {
            "suggestion": best_name,
            "confidence": best_score / 100.0,
        }

    async def auto_map_all(
        self, raw_genres: list[str], threshold: int = 80
    ) -> dict[str, dict | None]:
        """Batch fuzzy match. Returns {raw_genre: {suggestion, confidence} | None}."""
        return {raw: await self.auto_map(raw, threshold) for raw in raw_genres}

    async def get_unmapped_genres(self, raw_genres: list[str]) -> list[str]:
        """Return raw genres that have no mapping."""
        return await self._store.get_unmapped_genres(raw_genres)

    async def get_all_mappings(self) -> list[dict]:
        """Return all raw → canonical mappings."""
        return await self._store.get_all_mappings()

    async def get_genre_stats(
        self, canonical_genre: str | None = None
    ) -> list[dict]:
        """Return track counts by canonical genre (optionally filtered)."""
        return await self._store.get_genre_stats(canonical_genre)

    async def scan_library_genres(self) -> list[str]:
        """Scan library_files for unique raw genres."""
        return await self._store.scan_library_genres()

    async def apply_auto_mappings(
        self, threshold: int = 80
    ) -> dict[str, str]:
        """Auto-map all unmapped raw genres in the library and save the mappings.
        Returns {raw_genre: canonical} for the new mappings."""
        raw_genres = await self._store.scan_library_genres()
        unmapped = await self._store.get_unmapped_genres(raw_genres)
        auto_results = await self.auto_map_all(unmapped, threshold=threshold)

        to_save: list[tuple[str, str, float]] = []
        applied: dict[str, str] = {}
        for raw, suggestion in auto_results.items():
            if suggestion:
                canonical = suggestion["suggestion"]
                confidence = suggestion["confidence"]
                to_save.append((raw, canonical, confidence))
                applied[raw] = canonical

        if to_save:
            await self._store.bulk_set_mappings(to_save)

        return applied
