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


# --- File rename from tags ---

class FileRenamePreviewRequest(AppStruct):
    file_ids: list[str]
    template: str = "{albumartist}/{album} ({year})/{track:02d} - {title}.{ext}"


class FileRenameItem(AppStruct):
    file_id: str
    title: str
    old_path: str
    new_path: str


class FileRenamePreviewResponse(AppStruct):
    items: list[FileRenameItem]
    total: int


class FileRenameApplyRequest(AppStruct):
    file_ids: list[str]
    template: str = "{albumartist}/{album} ({year})/{track:02d} - {title}.{ext}"


class FileRenameApplyResponse(AppStruct):
    renamed: int
    failed: int
    errors: list[dict] = []
