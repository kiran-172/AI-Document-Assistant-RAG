
import os
import secrets
import hashlib

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from backend.database import SessionLocal


# --------------------------------------------------
# Configuration
# --------------------------------------------------

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

password_hasher = PasswordHash.recommended()

SESSION_COOKIE_NAME = "kiranai_session"
SESSION_DURATION_DAYS = 7

COOKIE_SECURE = (
    os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
)


# --------------------------------------------------
# Request Schemas
# --------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


# --------------------------------------------------
# Session Utilities
# --------------------------------------------------

def hash_session_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_session(db, user_id: str) -> str:

    token = secrets.token_urlsafe(32)
    token_hash = hash_session_token(token)

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(days=SESSION_DURATION_DAYS)
    )

    db.execute(
        text("""
            INSERT INTO user_sessions (
                user_id,
                token_hash,
                expires_at
            )
            VALUES (
                CAST(:user_id AS UUID),
                :token_hash,
                :expires_at
            )
        """),
        {
            "user_id": user_id,
            "token_hash": token_hash,
            "expires_at": expires_at
        }
    )

    return token


def set_session_cookie(response: Response, token: str):

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=SESSION_DURATION_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        path="/"
    )


# --------------------------------------------------
# User Authentication Dependency
# --------------------------------------------------

def get_current_user(request: Request):

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue."
        )

    token_hash = hash_session_token(token)

    db = SessionLocal()

    try:

        user = db.execute(
            text("""
                SELECT
                    u.id,
                    u.email,
                    u.role,
                    u.is_verified,
                    u.is_active
                FROM user_sessions s
                INNER JOIN users u
                    ON u.id = s.user_id
                WHERE
                    s.token_hash = :token_hash
                    AND s.revoked_at IS NULL
                    AND s.expires_at > CURRENT_TIMESTAMP
                    AND u.is_active = TRUE
            """),
            {"token_hash": token_hash}
        ).mappings().first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Your session is invalid or expired."
            )

        return dict(user)

    finally:
        db.close()


# --------------------------------------------------
# 1. User Registration
# --------------------------------------------------

@router.post("/register", status_code=201)
def register_user(request: RegisterRequest):

    email = str(request.email).strip().lower()

    db = SessionLocal()

    try:

        user_id = db.execute(
            text("""
                INSERT INTO users (
                    email,
                    password_hash,
                    role
                )
                VALUES (
                    :email,
                    :password_hash,
                    'user'
                )
                RETURNING id
            """),
            {
                "email": email,
                "password_hash": password_hasher.hash(
                    request.password
                )
            }
        ).scalar_one()

        db.commit()

        return {
            "message": "Registration successful. Please log in.",
            "user_id": str(user_id),
            "email": email,
            "role": "user"
        }

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists."
        )

    except Exception:

        db.rollback()
        raise

    finally:
        db.close()


# --------------------------------------------------
# 2. User Login
# --------------------------------------------------

@router.post("/login")
def login_user(
    request: LoginRequest,
    response: Response
):

    email = str(request.email).strip().lower()

    db = SessionLocal()

    try:

        user = db.execute(
            text("""
                SELECT
                    id,
                    email,
                    password_hash,
                    role,
                    is_active
                FROM users
                WHERE LOWER(email) = :email
            """),
            {"email": email}
        ).mappings().first()

        if not user or not password_hasher.verify(
            request.password,
            user["password_hash"]
        ):

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        if not user["is_active"]:

            raise HTTPException(
                status_code=403,
                detail="This account is disabled."
            )

        token = create_session(
            db,
            str(user["id"])
        )

        db.commit()

        set_session_cookie(response, token)

        return {
            "message": "Login successful.",
            "user": {
                "id": str(user["id"]),
                "email": user["email"],
                "role": user["role"]
            }
        }

    finally:
        db.close()


# --------------------------------------------------
# 3. Get Current Logged-in User
# --------------------------------------------------

@router.get("/me")
def get_my_account(
    current_user: dict = Depends(get_current_user)
):

    return {
        "user": {
            "id": str(current_user["id"]),
            "email": current_user["email"],
            "role": current_user["role"],
            "is_verified": current_user["is_verified"]
        }
    }


# --------------------------------------------------
# 4. User Logout
# --------------------------------------------------

@router.post("/logout")
def logout_user(
    response: Response,
    request: Request
):

    token = request.cookies.get(SESSION_COOKIE_NAME)

    if token:

        db = SessionLocal()

        try:

            db.execute(
                text("""
                    UPDATE user_sessions
                    SET revoked_at = CURRENT_TIMESTAMP
                    WHERE
                        token_hash = :token_hash
                        AND revoked_at IS NULL
                """),
                {
                    "token_hash": hash_session_token(token)
                }
            )

            db.commit()

        finally:
            db.close()

    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax"
    )

    return {
        "message": "Logout successful."
    }
# --------------------------------------------------
# Admin Authorization Dependency
# --------------------------------------------------

def require_admin(
    current_user: dict = Depends(get_current_user)
):
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )

    return current_user