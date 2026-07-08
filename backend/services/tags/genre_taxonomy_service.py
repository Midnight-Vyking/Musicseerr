"""GenreTaxonomyService - taxonomy loading, lookup, fuzzy matching."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

_TAXONOMY_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "genre_taxonomy.yaml"


class GenreTaxonomyService:
    """Loads the genre taxonomy YAML and provides lookup + fuzzy matching."""

    def __init__(self, taxonomy_path: Path | None = None):
        self._path = taxonomy_path or _TAXONOMY_PATH
        self._canonical: dict[str, str] = {}  # lowercase -> display name
        self._category_map: dict[str, list[str]] = {}  # category -> canonical names
        self._genre_to_categories: dict[str, list[str]] = {}  # canonical -> categories
        self._all_genres: list[str] = []
        self._loaded = False

    def load(self) -> None:
        if self._loaded:
            return
        with open(self._path) as f:
            data = yaml.safe_load(f)
        self._canonical = {}
        self._category_map = {}
        self._genre_to_categories = {}
        for category in data.get("categories", []):
            cat_name = category["name"]
            genres = category.get("genres", [])
            self._category_map.setdefault(cat_name, [])
            for genre in genres:
                low = genre.lower()
                self._canonical[low] = genre
                self._category_map.setdefault(cat_name, []).append(genre)
                self._genre_to_categories.setdefault(genre, []).append(cat_name)
        self._all_genres = sorted(self._canonical.values())
        self._loaded = True

    @property
    def all_genres(self) -> list[str]:
        if not self._loaded:
            self.load()
        return self._all_genres

    @property
    def categories(self) -> list[str]:
        if not self._loaded:
            self.load()
        return list(self._category_map.keys())

    def get_genres_in_category(self, category: str) -> list[str]:
        if not self._loaded:
            self.load()
        return self._category_map.get(category, [])

    def get_categories_for_genre(self, genre: str) -> list[str]:
        if not self._loaded:
            self.load()
        return self._genre_to_categories.get(genre, [])

    def is_canonical(self, genre: str) -> bool:
        if not self._loaded:
            self.load()
        return genre.lower() in self._canonical

    def fuzzy_match(self, raw_genre: str, threshold: int = 80) -> list[tuple[str, int]]:
        """Fuzzy match a raw genre string against the taxonomy.

        Returns (canonical_name, score) sorted by score desc.
        """
        if not self._loaded:
            self.load()
        raw_lower = raw_genre.lower().strip()
        # Exact match first
        if raw_lower in self._canonical:
            return [(self._canonical[raw_lower], 100)]
        # Fuzzy match
        results: list[tuple[str, int]] = []
        for canonical_lower, display in self._canonical.items():
            score = fuzz.token_sort_ratio(raw_lower, canonical_lower)
            if score >= threshold:
                results.append((display, score))
        results.sort(key=lambda x: x[1], reverse=True)
        # Token set ratio as tiebreaker
        if len(results) > 1 and results[0][1] == results[1][1]:
            refined = [
                (name, fuzz.token_set_ratio(raw_lower, name.lower()))
                for name, _ in results
            ]
            refined.sort(key=lambda x: x[1], reverse=True)
            return [(n, s) for n, s in refined if s >= threshold]
        return results[:5]  # top 5
