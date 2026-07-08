"""Tests for FileRenamerService — template resolution and preview."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.tags.file_renamer_service import (
    FileRenamerService,
    resolve_template,
    safe_path_component,
)


class TestSafePathComponent:
    def test_basic(self):
        assert safe_path_component("Hello") == "Hello"

    def test_removes_slashes(self):
        assert safe_path_component("foo/bar") == "foo-bar"

    def test_removes_null(self):
        assert safe_path_component("foo\x00bar") == "foo-bar"

    def test_removes_ugly_chars(self):
        safe = safe_path_component('foo:bar*baz?<>.txt"')
        assert "/" not in safe
        assert "\x00" not in safe

    def test_trims_dots(self):
        assert safe_path_component("...hello.") == "hello"

    def test_truncates_long(self):
        long = "a" * 200
        result = safe_path_component(long, max_length=50)
        assert len(result) <= 50

    def test_truncates_preserves_ext(self):
        long = "a" * 200 + ".flac"
        result = safe_path_component(long, max_length=50)
        assert result.endswith(".flac")
        assert len(result) <= 50

    def test_empty_becomes_unknown(self):
        assert safe_path_component("") == "unknown"
        assert safe_path_component("...") == "unknown"


class TestResolveTemplate:
    def _tag(self, **overrides) -> dict:
        base = {
            "artist": "Radiohead",
            "album": "OK Computer",
            "title": "Airbag",
            "album_artist": "Radiohead",
            "track_number": 1,
            "disc_number": 1,
            "year": 1997,
            "genre": "Alternative Rock",
            "file_path": "/music/Radiohead/OK Computer/01 - Airbag.flac",
            "release_group_mbid": "b1392450-e666-3926-a536-22c65f834433",
        }
        base.update(overrides)
        return base

    def test_simple_template(self):
        result = resolve_template("{artist} - {title}", self._tag())
        assert result == "Radiohead - Airbag"

    def test_directory_template(self):
        result = resolve_template(
            "{albumartist}/{album} ({year})/{track:02d} - {title}.{ext}",
            self._tag(),
        )
        assert result.startswith("Radiohead/OK Computer (1997)/01 - Airbag.flac")

    def test_padded_track(self):
        result = resolve_template("{track:02d}", self._tag())
        assert result == "01"

        result2 = resolve_template("{track:03d}", self._tag())
        assert result2 == "001"

    def test_padded_disc(self):
        result = resolve_template("{disc:02d}", self._tag(disc_number=2))
        assert result == "02"

    def test_ext_from_path(self):
        tag = self._tag(file_path="/music/Radiohead/OK Computer/01 - Airbag.flac")
        result = resolve_template("{ext}", tag)
        assert result == "flac"

    def test_unknown_ext(self):
        tag = self._tag(file_path="/music/Radiohead/OK Computer/01 - Airbag")
        result = resolve_template("{ext}", tag)
        assert result == ""

    def test_missing_fields_default(self):
        tag = self._tag()
        tag.pop("artist", None)
        result = resolve_template("{artist}", tag)
        assert result == "Unknown Artist"

    def test_mbid(self):
        result = resolve_template("{mbid}", self._tag())
        assert result == "b1392450-e666-3926-a536-22c65f834433"

    def test_genre(self):
        result = resolve_template("{genre}", self._tag())
        assert result == "Alternative Rock"


class TestFileRenamerService:
    """Tests that hit only template logic, not the filesystem."""

    @pytest.fixture
    def svc(self) -> FileRenamerService:
        return FileRenamerService(MagicMock(), MagicMock())

    @pytest.mark.asyncio
    async def test_preview_skips_missing_file(self, svc):
        svc._db.get_library_file_by_id = MagicMock(return_value=None)
        items = await svc.preview(["no-such-id"], "{artist} - {title}.{ext}")
        assert items == []
