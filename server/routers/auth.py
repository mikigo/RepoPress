from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from schemas import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from services import (
    authenticate_user,
    create_access_token,
    get_user_by_id,
    verify_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserResponse:
    """Dependency to get the current authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = verify_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    from uuid import UUID
    user_id = UUID(payload.get("sub"))
    user = await get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive",
        )

    return UserResponse.model_validate(user)


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate a user and return a JWT token."""
    user = await authenticate_user(body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    access_token = create_access_token(user)
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post("/logout")
async def logout():
    """Logout the current user.

    Client-side token invalidation. The frontend should discard the token.
    """
    return {"message": "Logged out successfully"}


@router.get("/user", response_model=UserResponse)
async def get_user(user: UserResponse = Depends(get_current_user)):
    """Get current authenticated user info."""
    return user
