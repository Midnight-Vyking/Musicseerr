"""Schemas for batch tag operations."""

from infrastructure.msgspec_fastapi import AppStruct


class TrackTagEntry(AppStruct):
    """One track's proposed tag update."""

    file_id: str
    title: str | None = None
    artist: str | None = None
    album: str | None = None
    track_number: int | None = None
    album_artist: str | None = None
    disc_number: int | None = None
    year: int | None = None
    genre: str | None = None


class BatchTagPreviewRequest(AppStruct):
    tags: list[TrackTagEntry]


class TagDiffEntry(AppStruct):
    """Before/after for one field on one track."""

    field: str
    old_value: str | None = None
    new_value: str | None = None


class BatchTagPreviewItem(AppStruct):
    file_id: str
    file_path: str
    title: str
    diffs: list[TagDiffEntry]


class BatchTagPreviewResponse(AppStruct):
    items: list[BatchTagPreviewItem]
    total: int


class BatchTagUpdateRequest(AppStruct):
    tags: list[TrackTagEntry]
    confirm: bool = False  # false = preview only; true = apply


class BatchTagUpdateResponse(AppStruct):
    updated: int
    failed: int
    errors: list[dict] = []
