"""Tests for GenreTaxonomyService."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
import yaml

from services.tags.genre_taxonomy_service import GenreTaxonomyService


@pytest.fixture
def taxonomy_yaml() -> str:
    """Create a minimal taxonomy YAML for testing."""
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
                    "Punk Rock",
                ],
            },
            {
                "name": "Electronic",
                "genres": [
                    "Ambient",
                    "House",
                    "Techno",
                    "Trance",
                    "Drum and Bass",
                ],
            },
            {
                "name": "Jazz",
                "genres": [
                    "Bebop",
                    "Cool Jazz",
                    "Fusion",
                    "Swing",
                ],
            },
        ]
    }
    return yaml.safe_dump(data)


@pytest.fixture
def taxonomy_path(taxonomy_yaml: str) -> str:
    """Write the taxonomy YAML to a temp file."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write(taxonomy_yaml)
        return f.name


@pytest.fixture
def svc(taxonomy_path: str) -> GenreTaxonomyService:
    """Create a GenreTaxonomyService with the test taxonomy."""
    return GenreTaxonomyService(taxonomy_path=Path(taxonomy_path))


class TestGenreTaxonomyService:
    """Tests for GenreTaxonomyService."""

    def test_load_populates_all_genres(self, svc: GenreTaxonomyService):
        svc.load()
        assert len(svc.all_genres) == 16  # 7 + 5 + 4 unique
        assert "Alternative Rock" in svc.all_genres
        assert "Ambient" in svc.all_genres
        assert "Bebop" in svc.all_genres

    def test_categories_property(self, svc: GenreTaxonomyService):
        svc.load()
        cats = svc.categories
        assert len(cats) == 3
        assert "Rock" in cats
        assert "Electronic" in cats
        assert "Jazz" in cats

    def test_get_genres_in_category(self, svc: GenreTaxonomyService):
        svc.load()
        rock_genres = svc.get_genres_in_category("Rock")
        assert len(rock_genres) == 7
        assert "Classic Rock" in rock_genres

    def test_get_genres_in_category_nonexistent(self, svc: GenreTaxonomyService):
        svc.load()
        assert svc.get_genres_in_category("Nonexistent") == []

    def test_get_categories_for_genre(self, svc: GenreTaxonomyService):
        svc.load()
        cats = svc.get_categories_for_genre("Techno")
        assert cats == ["Electronic"]

    def test_get_categories_for_genre_not_found(self, svc: GenreTaxonomyService):
        svc.load()
        assert svc.get_categories_for_genre("Nonexistent") == []

    def test_is_canonical_true(self, svc: GenreTaxonomyService):
        svc.load()
        assert svc.is_canonical("Alternative Rock") is True
        # Case-insensitive
        assert svc.is_canonical("alternative rock") is True

    def test_is_canonical_false(self, svc: GenreTaxonomyService):
        svc.load()
        assert svc.is_canonical("Garage Punk") is False

    def test_fuzzy_match_exact(self, svc: GenreTaxonomyService):
        svc.load()
        matches = svc.fuzzy_match("Techno")
        assert len(matches) == 1
        assert matches[0] == ("Techno", 100)

    def test_fuzzy_match_case_insensitive(self, svc: GenreTaxonomyService):
        svc.load()
        matches = svc.fuzzy_match("techno")
        assert len(matches) == 1
        assert matches[0] == ("Techno", 100)

    def test_fuzzy_match_close_match(self, svc: GenreTaxonomyService):
        svc.load()
        # "Progressive Rok" should fuzzy match to "Progressive Rock"
        matches = svc.fuzzy_match("Progressive Rok", threshold=70)
        assert len(matches) > 0
        # The top match should be Progressive Rock
        assert "Progressive Rock" in [m[0] for m in matches]

    def test_fuzzy_match_no_match(self, svc: GenreTaxonomyService):
        svc.load()
        matches = svc.fuzzy_match("xyzzy_not_a_genre", threshold=80)
        assert matches == []

    def test_fuzzy_match_threshold_respected(self, svc: GenreTaxonomyService):
        svc.load()
        # With threshold=100, only exact matches should pass
        matches = svc.fuzzy_match("Punk", threshold=100)
        assert not matches  # "Punk" alone isn't canonical, "Punk Rock" isn't exact

    def test_lazy_loading(self, taxonomy_path: str):
        """Verify the taxonomy is lazy-loaded on first access."""
        svc = GenreTaxonomyService(taxonomy_path=Path(taxonomy_path))
        assert svc._loaded is False
        # Accessing a property triggers load
        _ = svc.all_genres
        assert svc._loaded is True

    def test_empty_taxonomy(self):
        """Test with an empty taxonomy."""
        data = {"categories": []}
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            yaml.safe_dump(data, f)
            path = f.name

        svc = GenreTaxonomyService(taxonomy_path=Path(path))
        svc.load()
        assert svc.all_genres == []
        assert svc.categories == []
