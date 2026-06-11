import asyncio
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Candidate, CandidateStatus, Score, User, UserRole, utcnow
from app.schemas import (
    CandidateDetailAdmin,
    CandidateDetailReviewer,
    CandidateListItemAdmin,
    CandidateListItemReviewer,
    CategoryAverage,
    InternalNotesUpdate,
    PaginatedCandidatesAdmin,
    PaginatedCandidatesReviewer,
    ScoreCreate,
    ScoreResponse,
    ScoreResponseAdmin,
)


DEFAULT_LIMIT = 20
MAX_LIMIT = 50


@dataclass
class UpsertScoreResult:
    score: Score
    created: bool


class CandidateService:
    def _clamp_pagination(self, offset: int, limit: int) -> tuple[int, int]:
        return max(offset, 0), min(max(limit, 1), MAX_LIMIT)

    def _apply_filters(
        self,
        query,
        *,
        status: str | None,
        role_applied: str | None,
        skill: str | None,
        keyword: str | None,
        is_admin: bool,
    ):
        if status:
            query = query.filter(Candidate.status == status)
        else:
            query = query.filter(Candidate.status != CandidateStatus.ARCHIVED.value)

        if not is_admin:
            query = query.filter(Candidate.status != CandidateStatus.ARCHIVED.value)

        if role_applied:
            query = query.filter(Candidate.role_applied == role_applied)

        if skill:
            skill_pattern = f'%"{skill}"%'
            query = query.filter(cast(Candidate.skills, String).like(skill_pattern))

        if keyword:
            pattern = f"%{keyword}%"
            query = query.filter(
                or_(
                    Candidate.name.ilike(pattern),
                    Candidate.email.ilike(pattern),
                    Candidate.role_applied.ilike(pattern),
                )
            )

        return query

    def _average_subquery(self, reviewer_id: str | None):
        avg_query = select(
            Score.candidate_id.label("candidate_id"),
            func.round(func.avg(Score.score), 1).label("avg_score"),
        ).group_by(Score.candidate_id)

        if reviewer_id is not None:
            avg_query = avg_query.where(Score.reviewer_id == reviewer_id)

        return avg_query.subquery()

    def _get_candidate_or_404(self, db: Session, candidate_id: str) -> Candidate:
        candidate = db.get(Candidate, candidate_id)
        if candidate is None or candidate.status == CandidateStatus.ARCHIVED.value:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        return candidate

    def list_candidates(
        self,
        db: Session,
        user: User,
        *,
        status: str | None = None,
        role_applied: str | None = None,
        skill: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = DEFAULT_LIMIT,
    ) -> PaginatedCandidatesAdmin | PaginatedCandidatesReviewer:
        offset, limit = self._clamp_pagination(offset, limit)
        is_admin = user.role == UserRole.ADMIN.value

        reviewer_id = None if is_admin else user.id
        avg_subq = self._average_subquery(reviewer_id)

        base_query = select(Candidate, avg_subq.c.avg_score).outerjoin(
            avg_subq, Candidate.id == avg_subq.c.candidate_id
        )
        base_query = self._apply_filters(
            base_query,
            status=status,
            role_applied=role_applied,
            skill=skill,
            keyword=keyword,
            is_admin=is_admin,
        )

        count_query = select(func.count(Candidate.id))
        count_query = self._apply_filters(
            count_query,
            status=status,
            role_applied=role_applied,
            skill=skill,
            keyword=keyword,
            is_admin=is_admin,
        )
        total = db.scalar(count_query) or 0

        rows = (
            db.execute(
                base_query.order_by(Candidate.created_at.desc()).offset(offset).limit(limit)
            )
            .all()
        )

        if is_admin:
            items = [
                CandidateListItemAdmin(
                    id=candidate.id,
                    name=candidate.name,
                    email=candidate.email,
                    role_applied=candidate.role_applied,
                    status=candidate.status,
                    skills=candidate.skills or [],
                    average_score=float(avg_score) if avg_score is not None else None,
                    created_at=candidate.created_at,
                )
                for candidate, avg_score in rows
            ]
            return PaginatedCandidatesAdmin(items=items, total=total, offset=offset, limit=limit)

        items = [
            CandidateListItemReviewer(
                id=candidate.id,
                name=candidate.name,
                email=candidate.email,
                role_applied=candidate.role_applied,
                status=candidate.status,
                skills=candidate.skills or [],
                my_average_score=float(avg_score) if avg_score is not None else None,
                created_at=candidate.created_at,
            )
            for candidate, avg_score in rows
        ]
        return PaginatedCandidatesReviewer(items=items, total=total, offset=offset, limit=limit)

    def _compute_average(
        self, db: Session, candidate_id: str, reviewer_id: str | None
    ) -> float | None:
        query = select(func.round(func.avg(Score.score), 1)).where(
            Score.candidate_id == candidate_id
        )
        if reviewer_id is not None:
            query = query.where(Score.reviewer_id == reviewer_id)
        result = db.scalar(query)
        return float(result) if result is not None else None

    def _compute_category_averages(self, db: Session, candidate_id: str) -> list[CategoryAverage]:
        rows = db.execute(
            select(Score.category, func.round(func.avg(Score.score), 1))
            .where(Score.candidate_id == candidate_id)
            .group_by(Score.category)
            .order_by(Score.category)
        ).all()
        return [CategoryAverage(category=cat, average=float(avg)) for cat, avg in rows]

    def get_candidate_detail(
        self, db: Session, user: User, candidate_id: str
    ) -> CandidateDetailAdmin | CandidateDetailReviewer:
        candidate = self._get_candidate_or_404(db, candidate_id)

        if user.role == UserRole.ADMIN.value:
            scores_query = (
                select(Score, User.email)
                .join(User, Score.reviewer_id == User.id)
                .where(Score.candidate_id == candidate_id)
                .order_by(Score.updated_at.desc())
            )
            score_rows = db.execute(scores_query).all()
            scores = [
                ScoreResponseAdmin(
                    id=score.id,
                    category=score.category,
                    score=score.score,
                    reviewer_id=score.reviewer_id,
                    reviewer_email=email,
                    note=score.note,
                    created_at=score.created_at,
                    updated_at=score.updated_at,
                )
                for score, email in score_rows
            ]
            return CandidateDetailAdmin(
                id=candidate.id,
                name=candidate.name,
                email=candidate.email,
                role_applied=candidate.role_applied,
                status=candidate.status,
                skills=candidate.skills or [],
                ai_summary=candidate.ai_summary,
                internal_notes=candidate.internal_notes,
                average_score=self._compute_average(db, candidate_id, reviewer_id=None),
                category_averages=self._compute_category_averages(db, candidate_id),
                scores=scores,
                created_at=candidate.created_at,
            )

        scores = (
            db.query(Score)
            .filter(Score.candidate_id == candidate_id, Score.reviewer_id == user.id)
            .order_by(Score.updated_at.desc())
            .all()
        )
        return CandidateDetailReviewer(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            role_applied=candidate.role_applied,
            status=candidate.status,
            skills=candidate.skills or [],
            ai_summary=candidate.ai_summary,
            my_average_score=self._compute_average(db, candidate_id, reviewer_id=user.id),
            scores=[ScoreResponse.model_validate(s) for s in scores],
            created_at=candidate.created_at,
        )

    def upsert_score(
        self,
        db: Session,
        user: User,
        candidate_id: str,
        payload: ScoreCreate,
    ) -> UpsertScoreResult:
        self._get_candidate_or_404(db, candidate_id)

        existing = (
            db.query(Score)
            .filter(
                Score.candidate_id == candidate_id,
                Score.reviewer_id == user.id,
                Score.category == payload.category.value,
            )
            .first()
        )

        if existing:
            existing.score = payload.score
            existing.note = payload.note
            existing.updated_at = utcnow()
            db.commit()
            db.refresh(existing)
            return UpsertScoreResult(score=existing, created=False)

        score = Score(
            candidate_id=candidate_id,
            reviewer_id=user.id,
            category=payload.category.value,
            score=payload.score,
            note=payload.note,
        )
        db.add(score)
        try:
            db.commit()
            db.refresh(score)
            return UpsertScoreResult(score=score, created=True)
        except IntegrityError:
            db.rollback()
            existing = (
                db.query(Score)
                .filter(
                    Score.candidate_id == candidate_id,
                    Score.reviewer_id == user.id,
                    Score.category == payload.category.value,
                )
                .first()
            )
            if existing is None:
                raise
            existing.score = payload.score
            existing.note = payload.note
            existing.updated_at = utcnow()
            db.commit()
            db.refresh(existing)
            return UpsertScoreResult(score=existing, created=False)

    async def generate_summary(
        self, db: Session, candidate_id: str, *, force: bool = False
    ) -> str:
        candidate = self._get_candidate_or_404(db, candidate_id)

        if candidate.ai_summary and not force:
            return candidate.ai_summary

        await asyncio.sleep(2)

        candidate.ai_summary = (
            f"Summary for {candidate.name} ({candidate.role_applied}): "
            f"Demonstrates solid experience across {', '.join(candidate.skills or ['general skills'])}. "
            f"Current pipeline status: {candidate.status}. "
            f"Recommended for continued review based on profile and scoring activity."
        )
        db.commit()
        db.refresh(candidate)
        return candidate.ai_summary

    def soft_delete(self, db: Session, candidate_id: str) -> None:
        candidate = self._get_candidate_or_404(db, candidate_id)
        candidate.status = CandidateStatus.ARCHIVED.value
        candidate.deleted_at = utcnow()
        db.commit()

    def update_internal_notes(
        self, db: Session, candidate_id: str, payload: InternalNotesUpdate
    ) -> None:
        candidate = self._get_candidate_or_404(db, candidate_id)
        candidate.internal_notes = payload.internal_notes
        db.commit()


candidate_service = CandidateService()
