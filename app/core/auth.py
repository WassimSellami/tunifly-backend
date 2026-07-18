"""Supabase access-token verification and authenticated-user dependency."""

import os
from dataclasses import dataclass
from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    id: str
    email: str


def _unauthorized(detail: str = "Invalid or missing Supabase access token") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


@lru_cache
def _jwks_client(supabase_url: str) -> jwt.PyJWKClient:
    return jwt.PyJWKClient(f"{supabase_url}/auth/v1/.well-known/jwks.json")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedUser:
    """Validate a Supabase JWT and return only trusted identity claims.

    Google OAuth happens in Supabase. The API never accepts an email or user ID
    from the request body as proof of identity.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise RuntimeError("SUPABASE_URL environment variable is not set")

    token = credentials.credentials
    try:
        algorithm = jwt.get_unverified_header(token).get("alg")
        if algorithm == "HS256":
            # Needed only for legacy Supabase projects that still issue HS256 JWTs.
            key = os.getenv("SUPABASE_JWT_SECRET")
            if not key:
                raise _unauthorized("SUPABASE_JWT_SECRET is not configured")
        elif algorithm in {"RS256", "ES256"}:
            key = _jwks_client(supabase_url).get_signing_key_from_jwt(token).key
        else:
            raise _unauthorized("Unsupported JWT signing algorithm")

        claims = jwt.decode(
            token,
            key,
            algorithms=[algorithm],
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )
    except HTTPException:
        raise
    except jwt.PyJWTError as exc:
        raise _unauthorized() from exc

    user_id = claims.get("sub")
    email = claims.get("email")
    if not isinstance(user_id, str) or not isinstance(email, str):
        raise _unauthorized("Token does not contain a user ID and email")
    return AuthenticatedUser(id=user_id, email=email)
