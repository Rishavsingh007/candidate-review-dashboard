from sqlalchemy.orm import Session

from app.auth import hash_password
from app.models import Candidate, CandidateStatus, User, UserRole

SEED_ADMIN_EMAIL = "admin@tech.com"
SEED_ADMIN_PASSWORD = "adminpass123"
SEED_REVIEWER_EMAILS = (
    ("reviewer1@tech.com", "reviewerpass123"),
    ("reviewer2@tech.com", "reviewerpass123"),
)

SAMPLE_CANDIDATES = [
    {
        "name": "Aisha Khan",
        "email": "aisha.khan@example.com",
        "role_applied": "Backend Engineer",
        "status": CandidateStatus.NEW.value,
        "skills": ["python", "fastapi", "postgresql"],
        "internal_notes": "Strong backend fundamentals; schedule technical screen.",
    },
    {
        "name": "Rohan Sharma",
        "email": "rohan.sharma@example.com",
        "role_applied": "Frontend Engineer",
        "status": CandidateStatus.REVIEWED.value,
        "skills": ["react", "typescript", "vite"],
        "internal_notes": "Portfolio looks polished; verify system design depth.",
    },
    {
        "name": "Emma Wilson",
        "email": "emma.wilson@example.com",
        "role_applied": "Full Stack Engineer",
        "status": CandidateStatus.NEW.value,
        "skills": ["python", "react", "docker"],
        "internal_notes": None,
    },
    {
        "name": "David Kim",
        "email": "david.kim@example.com",
        "role_applied": "Backend Engineer",
        "status": CandidateStatus.HIRED.value,
        "skills": ["go", "kubernetes", "aws"],
        "internal_notes": "Offer accepted.",
    },
    {
        "name": "Eva Patel",
        "email": "eva.patel@example.com",
        "role_applied": "Data Engineer",
        "status": CandidateStatus.REJECTED.value,
        "skills": ["python", "spark", "sql"],
        "internal_notes": "Not a fit for current opening.",
    },
    {
        "name": "Frank Lopez",
        "email": "frank.lopez@example.com",
        "role_applied": "Frontend Engineer",
        "status": CandidateStatus.NEW.value,
        "skills": ["react", "css", "accessibility"],
        "internal_notes": "Referral from engineering team.",
    },
    {
        "name": "Grace Wilson",
        "email": "grace.wilson@example.com",
        "role_applied": "Full Stack Engineer",
        "status": CandidateStatus.REVIEWED.value,
        "skills": ["node", "react", "mongodb"],
        "internal_notes": "Good communication in initial call.",
    },
    {
        "name": "Henry Brown",
        "email": "henry.brown@example.com",
        "role_applied": "Backend Engineer",
        "status": CandidateStatus.NEW.value,
        "skills": ["java", "spring", "kafka"],
        "internal_notes": None,
    },
    {
        "name": "James Brown",
        "email": "james.brown@example.com",
        "role_applied": "DevOps Engineer",
        "status": CandidateStatus.REVIEWED.value,
        "skills": ["terraform", "aws", "ci/cd"],
        "internal_notes": "Needs follow-up on on-call experience.",
    },
    {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role_applied": "Full Stack Engineer",
        "status": CandidateStatus.NEW.value,
        "skills": ["python", "react", "graphql"],
        "internal_notes": "Career switcher with strong portfolio project.",
    },
]


def _get_or_create_user(
    db: Session, email: str, password: str, role: UserRole
) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role.value,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_demo_data(db: Session) -> None:
    _get_or_create_user(db, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD, UserRole.ADMIN)

    for email, password in SEED_REVIEWER_EMAILS:
        _get_or_create_user(db, email, password, UserRole.REVIEWER)

    existing_count = db.query(Candidate).count()
    if existing_count >= len(SAMPLE_CANDIDATES):
        return

    for data in SAMPLE_CANDIDATES:
        exists = db.query(Candidate).filter(Candidate.email == data["email"]).first()
        if exists:
            continue
        db.add(Candidate(**data))

    db.commit()
