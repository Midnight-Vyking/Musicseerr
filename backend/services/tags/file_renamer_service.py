"""FileRenamerService - rename/move audio files based on tag templates.

Supports mp3tag-style templates: {artist}, {album}, {year}, {track:02d}, etc.
Generates previews and applies renames, updating the library DB after each move."""

from __future__ import annotations

import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import TYPE_CHECKING

from api.v1.schemas.tags import FileRenameItem

if TYPE_CHECKING:
    from infrastructure.audio.tagger import AudioTagger
    from infrastructure.persistence.library_db import LibraryDB

logger = logging.getLogger(__name__)

# Characters unsafe in filesystem paths (Linux allows everything except / and \0)
_UNSAFE_PATH_CHARS = re.compile(r'[/\x00]')
# Characters that are fine technically but ugly/painful in paths
_UGLY_PATH_CHARS = re.compile(r'[:*?"<>|]')
# Leading/trailing dots and spaces cause issues
_CLEAN_DOTS = re.compile(r'\.+$')
_CLEAN_LEADING = re.compile(r'^\.+')


def safe_path_component(value: str, max_length: int = 120) -> str:
    """Sanitize a single path component (file or folder name)."""
    # Normalize unicode
    value = unicodedata.normalize('NFC', value)
    # Replace unsafe chars
    value = _UNSAFE_PATH_CHARS.sub('-', value)
    value = _UGLY_PATH_CHARS.sub('', value)
    # Remove leading/trailing dots and spaces
    value = _CLEAN_LEADING.sub('', value)
    value = _CLEAN_DOTS.sub('', value)
    value = value.strip()
    # Truncate
    if len(value) > max_length:
        # Keep extension intact if present
        if '.' in value:
            base, ext = value.rsplit('.', 1)
            base = base[:max_length - len(ext) - 1]
            value = f"{base}.{ext}"
        else:
            value = value[:max_length]
    return value or "unknown"


def resolve_template(template: str, tag: dict) -> str:
    """Resolve a template string using tag values.

    Supported variables:
        {artist}, {album}, {title}, {year}, {albumartist},
        {track}, {track:02d}, {disc}, {disc:02d},
        {ext}, {genre}, {mbid}
    """
    result = template

    # Simple replacements
    simple_vars = {
        'artist': tag.get('artist', 'Unknown Artist'),
        'album': tag.get('album', 'Unknown Album'),
        'title': tag.get('title', 'Unknown Track'),
        'year': str(tag.get('year', '')) if tag.get('year') else '0000',
        'albumartist': tag.get('album_artist') or tag.get('artist', 'Unknown Artist'),
        'ext': Path(tag.get('file_path', '')).suffix.lstrip('.') or '',
        'genre': tag.get('genre', ''),
        'mbid': tag.get('release_group_mbid', ''),
    }

    for var, default in simple_vars.items():
        result = result.replace(f'{{{var}}}', default or '')

    # Padded track number: {track:02d}
    track_pad = re.findall(r'\{track:(\d+)d\}', result)
    for width in track_pad:
        val = str(tag.get('track_number', 0) or 0).zfill(int(width))
        result = result.replace(f'{{track:{width}d}}', val)
    result = result.replace('{track}', str(tag.get('track_number', 0) or 0))

    # Padded disc number: {disc:02d}
    disc_pad = re.findall(r'\{disc:(\d+)d\}', result)
    for width in disc_pad:
        val = str(tag.get('disc_number', 1) or 1).zfill(int(width))
        result = result.replace(f'{{disc:{width}d}}', val)
    result = result.replace('{disc}', str(tag.get('disc_number', 1) or 1))

    return result


class FileRenamerService:
    """Preview and apply file renames based on tag templates."""

    def __init__(self, tagger: AudioTagger, library_db: LibraryDB):
        self._tagger = tagger
        self._db = library_db

    async def preview(
        self, file_ids: list[str], template: str, library_root: Path | None = None
    ) -> list[FileRenameItem]:
        """Compute old_path → new_path for each file without moving anything."""
        results: list[FileRenameItem] = []
        for file_id in file_ids:
            try:
                row = await self._db.get_library_file_by_id(file_id)
                if not row:
                    continue
                old_path = Path(row['file_path'])
                old_tag, _ = self._tagger.read_tags(old_path)

                # Build tag dict for template resolution
                tag_dict = {
                    'artist': old_tag.artist,
                    'album': old_tag.album,
                    'title': old_tag.title,
                    'album_artist': old_tag.album_artist,
                    'track_number': old_tag.track_number,
                    'disc_number': old_tag.disc_number,
                    'year': old_tag.year,
                    'genre': old_tag.genre,
                    'file_path': str(old_path),
                    'release_group_mbid': old_tag.musicbrainz_release_group_id,
                }

                new_rel = resolve_template(template, tag_dict)
                parent = old_path.parent

                # If library_root is provided, use it as base
                if library_root and old_path.is_relative_to(library_root):
                    new_full = library_root / new_rel
                else:
                    new_full = parent / Path(new_rel).name

                results.append(FileRenameItem(
                    file_id=file_id,
                    title=old_tag.title,
                    old_path=str(old_path),
                    new_path=str(new_full),
                ))
            except Exception:
                logger.warning("Preview failed for file %s", file_id, exc_info=True)
        return results

    async def apply_rename(
        self, file_ids: list[str], template: str, library_root: Path | None = None
    ) -> tuple[int, int, list[dict]]:
        """Rename files on disk and update paths in the library DB.

        Each file is renamed atomically. On failure for one file, we continue
        with the next. Returns (renamed, failed, errors).
        """
        # First compute all new paths
        preview_items = await self.preview(file_ids, template, library_root)
        path_map = {item.file_id: item.new_path for item in preview_items}

        renamed = 0
        failed = 0
        errors: list[dict] = []

        for file_id in file_ids:
            new_path_str = path_map.get(file_id)
            if not new_path_str:
                failed += 1
                errors.append({'file_id': file_id, 'error': 'Could not compute new path'})
                continue

            try:
                row = await self._db.get_library_file_by_id(file_id)
                if not row:
                    failed += 1
                    errors.append({'file_id': file_id, 'error': 'File not found in library'})
                    continue

                old_path = Path(row['file_path'])
                new_path = Path(new_path_str)

                # Skip if same path
                if old_path.resolve() == new_path.resolve():
                    renamed += 1
                    continue

                # Create parent dirs
                new_path.parent.mkdir(parents=True, exist_ok=True)

                # Atomic rename
                os.rename(str(old_path), str(new_path))

                # Update DB path
                await self._db.update_file_path(file_id, str(new_path), old_path.stat().st_size)

                # Clean up empty directories
                try:
                    old_parent = old_path.parent
                    if old_parent.is_dir() and not any(old_parent.iterdir()):
                        old_parent.rmdir()
                except OSError:
                    pass

                renamed += 1
            except Exception as e:
                failed += 1
                errors.append({'file_id': file_id, 'error': str(e)})
                logger.warning("Rename failed for %s: %s", file_id, e, exc_info=True)

        return renamed, failed, errors
