from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, hash_password, verify_password
from app.models import User, UserRole
from app.schemas import UserLogin, UserRegister


class AuthService:
    def register(self, db: Session, payload: UserRegister) -> User:
        existing = db.query(User).filter(User.email == payload.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            role=UserRole.REVIEWER.value,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def login(self, db: Session, payload: UserLogin) -> str:
        user = db.query(User).filter(User.email == payload.email).first()
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
            )

        return create_access_token(user_id=user.id, role=user.role)


auth_service = AuthService()
