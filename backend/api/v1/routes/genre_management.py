"""Genre management endpoints — taxonomy, mappings, scan, stats.

All endpoints require admin authentication.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from infrastructure.msgspec_fastapi import AppStruct, MsgSpecBody, MsgSpecRoute
from middleware import CurrentAdminDep

logger = logging.getLogger(__name__)


async def _admin_guard(_: CurrentAdminDep) -> None: ...


router = APIRouter(
    route_class=MsgSpecRoute,
    prefix="/genre",
    tags=["genre"],
    dependencies=[Depends(_admin_guard)],
)


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class GenreMappingEntry(AppStruct):
    raw_genre: str
    canonical_genre: str
    confidence: float = 1.0


class SetMappingRequest(AppStruct):
    raw_genre: str
    canonical_genre: str
    confidence: float = 1.0


class AutoMapResult(AppStruct):
    raw_genre: str
    suggestion: str | None = None
    confidence: float | None = None


class ApplyAutoRequest(AppStruct):
    threshold: int = 80


class ApplyAutoResponse(AppStruct):
    applied: int
    mappings: dict[str, str] = {}


class GenreStatEntry(AppStruct):
    canonical_genre: str
    track_count: int


class ScanResponse(AppStruct):
    total_found: int
    raw_genres: list[str]


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_genre_taxonomy_svc() -> "GenreTaxonomyService":
    from core.dependencies._registry import singleton

    @singleton
    def _inner():
        from services.tags.genre_taxonomy_service import GenreTaxonomyService

        return GenreTaxonomyService()

    return _inner()


def get_genre_mapping_store() -> "GenreMappingStore":
    from core.dependencies._registry import singleton

    @singleton
    def _inner():
        from core.dependencies.cache_providers import (
            get_persistence_write_lock,
        )
        from core.config import get_settings
        from infrastructure.persistence.genre_mapping_store import (
            GenreMappingStore,
        )

        settings = get_settings()
        lock = get_persistence_write_lock()
        return GenreMappingStore(
            db_path=settings.library_db_path, write_lock=lock
        )

    return _inner()


def get_genre_mapping_svc() -> "GenreMappingService":
    from core.dependencies._registry import singleton

    @singleton
    def _inner():
        from services.tags.genre_mapping_service import GenreMappingService

        return GenreMappingService(
            taxonomy=get_genre_taxonomy_svc(),
            store=get_genre_mapping_store(),
        )

    return _inner()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/mappings", response_model=list[GenreMappingEntry])
async def list_mappings(
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    mappings = await mapping_svc.get_all_mappings()
    return [GenreMappingEntry(**m) for m in mappings]


@router.post("/mappings", response_model=GenreMappingEntry)
async def set_mapping(
    body: SetMappingRequest = MsgSpecBody(SetMappingRequest),
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    await mapping_svc.set_mapping(body.raw_genre, body.canonical_genre, body.confidence)
    return GenreMappingEntry(
        raw_genre=body.raw_genre,
        canonical_genre=body.canonical_genre,
        confidence=body.confidence,
    )


@router.post("/mappings/auto-map", response_model=list[AutoMapResult])
async def auto_map_suggestions(
    raw_genres: list[str] = MsgSpecBody(list[str]),
    threshold: int = Query(80),
    taxonomy_svc: "GenreTaxonomyService" = Depends(get_genre_taxonomy_svc),
):
    results: list[AutoMapResult] = []
    for raw in raw_genres:
        matches = taxonomy_svc.fuzzy_match(raw, threshold=threshold)
        if matches:
            results.append(
                AutoMapResult(
                    raw_genre=raw,
                    suggestion=matches[0][0],
                    confidence=matches[0][1] / 100.0,
                )
            )
        else:
            results.append(
                AutoMapResult(raw_genre=raw, suggestion=None, confidence=None)
            )
    return results


@router.post("/mappings/apply-auto", response_model=ApplyAutoResponse)
async def apply_auto_mappings(
    body: ApplyAutoRequest = MsgSpecBody(ApplyAutoRequest),
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    applied = await mapping_svc.apply_auto_mappings(threshold=body.threshold)
    return ApplyAutoResponse(applied=len(applied), mappings=applied)


@router.get("/taxonomy")
async def get_taxonomy(
    taxonomy_svc: "GenreTaxonomyService" = Depends(get_genre_taxonomy_svc),
):
    """Return the full taxonomy (categories with their genres) as JSON."""
    taxonomy_svc.load()
    result: list[dict[str, Any]] = []
    for cat in taxonomy_svc.categories:
        result.append(
            {
                "name": cat,
                "genres": taxonomy_svc.get_genres_in_category(cat),
            }
        )
    return {"categories": result}


@router.get("/taxonomy/categories", response_model=list[str])
async def get_taxonomy_categories(
    taxonomy_svc: "GenreTaxonomyService" = Depends(get_genre_taxonomy_svc),
):
    return taxonomy_svc.categories


@router.get("/unmapped", response_model=list[str])
async def get_unmapped_genres(
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    raw_genres = await mapping_svc.scan_library_genres()
    unmapped = await mapping_svc.get_unmapped_genres(raw_genres)
    return unmapped


@router.get("/stats", response_model=list[GenreStatEntry])
async def get_genre_stats(
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    stats = await mapping_svc.get_genre_stats()
    return [GenreStatEntry(**s) for s in stats]


@router.post("/scan", response_model=ScanResponse)
async def scan_library_genres(
    mapping_svc: "GenreMappingService" = Depends(get_genre_mapping_svc),
):
    raw_genres = await mapping_svc.scan_library_genres()
    return ScanResponse(total_found=len(raw_genres), raw_genres=raw_genres)
