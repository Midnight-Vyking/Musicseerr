"""Routes for tag-based file rename operations."""

import logging

from fastapi import APIRouter, Depends

from api.v1.schemas.tags import (
    FileRenameApplyRequest,
    FileRenameApplyResponse,
    FileRenamePreviewRequest,
    FileRenamePreviewResponse,
)
from infrastructure.msgspec_fastapi import MsgSpecBody, MsgSpecRoute
from middleware import CurrentAdminDep
from services.tags.file_renamer_service import FileRenamerService

logger = logging.getLogger(__name__)

router = APIRouter(
    route_class=MsgSpecRoute,
    prefix="/library/tracks/rename",
    tags=["file-rename"],
)


async def _get_renamer(
    _admin: CurrentAdminDep,
) -> FileRenamerService:
    from core.dependencies.service_providers import get_audio_tagger, get_library_db

    tagger = get_audio_tagger()
    db = get_library_db()
    return FileRenamerService(tagger, db)


@router.post("/preview", response_model=FileRenamePreviewResponse)
async def preview_rename(
    body: FileRenamePreviewRequest = MsgSpecBody(FileRenamePreviewRequest),
    renamer: FileRenamerService = Depends(_get_renamer),
):
    items = await renamer.preview(body.file_ids, body.template)
    return FileRenamePreviewResponse(items=items, total=len(items))


@router.post("/apply", response_model=FileRenameApplyResponse)
async def apply_rename(
    body: FileRenameApplyRequest = MsgSpecBody(FileRenameApplyRequest),
    renamer: FileRenamerService = Depends(_get_renamer),
):
    renamed, failed, errors = await renamer.apply_rename(
        body.file_ids, body.template
    )
    return FileRenameApplyResponse(renamed=renamed, failed=failed, errors=errors)
