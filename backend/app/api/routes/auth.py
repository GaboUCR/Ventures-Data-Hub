# app/api/routes/auth.py
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select, insert
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import engine
from app.db.tables import users, companies, company_memberships
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


# --------- Schemas ---------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    company_name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    company_id: Optional[str] = None
    full_name: Optional[str] = None
    global_role: str


# --------- Helpers ---------

def _get_user_by_email(email: str):
    with engine.begin() as conn:
        stmt = select(
            users.c.id,
            users.c.email,
            users.c.password_hash,
            users.c.full_name,
            users.c.global_role,
        ).where(users.c.email == email)
        row = conn.execute(stmt).first()
        return row


def _get_primary_company_for_user(user_id: str) -> Optional[str]:
    with engine.begin() as conn:
        stmt = select(company_memberships.c.company_id).where(
            company_memberships.c.user_id == user_id,
            company_memberships.c.is_primary_owner == True,  # noqa: E712
        )
        row = conn.execute(stmt).first()
        return str(row.company_id) if row else None


# --------- Routes ---------

@router.post("/signup", response_model=TokenResponse)
def signup(payload: SignupRequest):
    """
    Signup flow for a company owner:
    - creates user
    - creates company
    - links them via company_memberships as primary owner
    - returns JWT
    """
    try:
        with engine.begin() as conn:
            # 1) Check if email already exists
            existing = _get_user_by_email(str(payload.email))
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists.",
                )

            # 2) Create user
            hashed = get_password_hash(payload.password)
            user_ins = (
                insert(users)
                .values(
                    email=str(payload.email),
                    password_hash=hashed,
                    full_name=payload.full_name,
                    global_role="company_user",
                )
                .returning(users.c.id, users.c.full_name, users.c.global_role)
            )
            user_res = conn.execute(user_ins).first()
            user_id = str(user_res.id)

            # 3) Create company
            company_ins = (
                insert(companies)
                .values(
                    name=payload.company_name,
                )
                .returning(companies.c.id)
            )
            company_res = conn.execute(company_ins).first()
            company_id = str(company_res.id)

            # 4) Create membership as primary owner
            membership_ins = insert(company_memberships).values(
                company_id=company_id,
                user_id=user_id,
                role="owner",
                is_primary_owner=True,
            )
            conn.execute(membership_ins)

        # 5) Create JWT
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token = create_access_token(
            subject=user_id,
            expires_delta=access_token_expires,
            extra_claims={
                "global_role": user_res.global_role,
                "company_id": company_id,
            },
        )

        return TokenResponse(
            access_token=token,
            user_id=user_id,
            company_id=company_id,
            full_name=user_res.full_name,
            global_role=user_res.global_role,
        )

    except HTTPException:
        # Reraise explicit HTTP errors
        raise
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error during signup: {e}",
        )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    """
    Basic email+password login.
    Returns JWT with user_id and (if any) primary company id.
    """
    row = _get_user_by_email(str(payload.email))
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not verify_password(payload.password, row.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    user_id = str(row.id)
    company_id = _get_primary_company_for_user(user_id)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        subject=user_id,
        expires_delta=access_token_expires,
        extra_claims={
            "global_role": row.global_role,
            "company_id": company_id,
        },
    )

    return TokenResponse(
        access_token=token,
        user_id=user_id,
        company_id=company_id,
        full_name=row.full_name,
        global_role=row.global_role,
    )
