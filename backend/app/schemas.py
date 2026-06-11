from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_serializer

from app.models import ScoreCategory


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


# --- Auth ---


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    role: str


# --- Scores ---


class ScoreCreate(BaseModel):
    category: ScoreCategory
    score: int = Field(ge=1, le=5)
    note: str | None = None


class ScoreResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: str
    score: int
    reviewer_id: str
    note: str | None
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetimes_utc(self, value: datetime) -> datetime:
        return _as_utc(value)


class ScoreResponseAdmin(ScoreResponse):
    reviewer_email: str | None = None


# --- Candidates (list) ---


class CandidateListItemAdmin(BaseModel):
    id: str
    name: str
    email: str
    role_applied: str
    status: str
    skills: list[str]
    average_score: float | None
    created_at: datetime


class CandidateListItemReviewer(BaseModel):
    id: str
    name: str
    email: str
    role_applied: str
    status: str
    skills: list[str]
    my_average_score: float | None
    created_at: datetime


class PaginatedCandidatesAdmin(BaseModel):
    items: list[CandidateListItemAdmin]
    total: int
    offset: int
    limit: int


class PaginatedCandidatesReviewer(BaseModel):
    items: list[CandidateListItemReviewer]
    total: int
    offset: int
    limit: int


# --- Candidates (detail) ---


class CategoryAverage(BaseModel):
    category: str
    average: float


class CandidateDetailAdmin(BaseModel):
    id: str
    name: str
    email: str
    role_applied: str
    status: str
    skills: list[str]
    ai_summary: str | None
    internal_notes: str | None
    average_score: float | None
    category_averages: list[CategoryAverage]
    scores: list[ScoreResponseAdmin]
    created_at: datetime


class CandidateDetailReviewer(BaseModel):
    id: str
    name: str
    email: str
    role_applied: str
    status: str
    skills: list[str]
    ai_summary: str | None
    my_average_score: float | None
    scores: list[ScoreResponse]
    created_at: datetime


class SummaryResponse(BaseModel):
    ai_summary: str


class InternalNotesUpdate(BaseModel):
    internal_notes: str
