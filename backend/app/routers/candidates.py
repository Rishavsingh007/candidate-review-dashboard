from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.auth import get_current_user, require_admin
from app.database import get_db
from app.models import User
from app.schemas import (
    CandidateDetailAdmin,
    CandidateDetailReviewer,
    InternalNotesUpdate,
    PaginatedCandidatesAdmin,
    PaginatedCandidatesReviewer,
    ScoreCreate,
    ScoreResponse,
    SummaryResponse,
)
from app.services.candidate_service import candidate_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedCandidatesAdmin | PaginatedCandidatesReviewer,
)
def list_candidates(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Annotated[str | None, Query()] = None,
    role_applied: Annotated[str | None, Query()] = None,
    skill: Annotated[str | None, Query()] = None,
    keyword: Annotated[str | None, Query()] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
):
    return candidate_service.list_candidates(
        db,
        current_user,
        status=status,
        role_applied=role_applied,
        skill=skill,
        keyword=keyword,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{candidate_id}",
    response_model=CandidateDetailAdmin | CandidateDetailReviewer,
)
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return candidate_service.get_candidate_detail(db, current_user, candidate_id)


@router.post(
    "/{candidate_id}/scores",
    response_model=ScoreResponse,
)
def upsert_score(
    candidate_id: str,
    payload: ScoreCreate,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = candidate_service.upsert_score(db, current_user, candidate_id, payload)
    response.status_code = (
        status.HTTP_201_CREATED if result.created else status.HTTP_200_OK
    )
    return ScoreResponse.model_validate(result.score)


@router.post("/{candidate_id}/summary", response_model=SummaryResponse)
async def generate_summary(
    candidate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    force: Annotated[bool, Query()] = False,
):
    _ = current_user
    summary = await candidate_service.generate_summary(db, candidate_id, force=force)
    return SummaryResponse(ai_summary=summary)


@router.patch(
    "/{candidate_id}/internal-notes",
    response_model=CandidateDetailAdmin,
)
def update_internal_notes(
    candidate_id: str,
    payload: InternalNotesUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    candidate_service.update_internal_notes(db, candidate_id, payload)
    return candidate_service.get_candidate_detail(db, admin, candidate_id)


@router.delete("/{candidate_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    candidate_service.soft_delete(db, candidate_id)
