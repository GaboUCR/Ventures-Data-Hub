# app/api/deps/auth.py
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.security import decode_access_token
from app.db.session import engine
from app.db.tables import users

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class CurrentUser(BaseModel):
    id: str
    company_id: Optional[str]
    global_role: str
    is_active: bool


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    try:
        payload = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user_id = payload.get("sub")
    token_company_id = payload.get("company_id")
    token_global_role = payload.get("global_role")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing subject",
        )

    try:
        with engine.begin() as conn:
            stmt = select(
                users.c.id,
                users.c.is_active,
                users.c.global_role,
            ).where(users.c.id == user_id)
            row = conn.execute(stmt).first()
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DB error fetching user: {e}",
        )

    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    if not row.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    global_role = token_global_role or row.global_role

    return CurrentUser(
        id=str(row.id),
        company_id=token_company_id,
        global_role=global_role,
        is_active=row.is_active,
    )
