from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from models import User
from schemas import (
    ErrorResponse,
    PermissionCreate,
    PermissionsUpdateRequest,
    RepoConfigCreate,
    RepoConfigResponse,
    RepoConfigUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from services import (
    create_repo,
    create_user,
    delete_repo,
    get_repo_by_id,
    get_repos,
    list_users,
    update_permissions,
    update_repo,
    update_user,
)
from routers.auth import get_current_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


async def require_admin(user: UserResponse = Depends(get_current_user)) -> UserResponse:
    """Dependency that ensures the current user is a superuser."""
    if not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


# ─── Repo Management ───────────────────────────────────────────────────


@router.post("/repos", response_model=RepoConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_repo_endpoint(
    body: RepoConfigCreate,
    _admin: UserResponse = Depends(require_admin),
):
    """Create a new repository configuration (admin only)."""
    repo = await create_repo(body)
    return RepoConfigResponse.model_validate(repo)


@router.get("/repos", response_model=list[RepoConfigResponse])
async def list_repos_endpoint(
    _admin: UserResponse = Depends(require_admin),
):
    """List all repository configurations."""
    repos = await get_repos()
    return [RepoConfigResponse.model_validate(r) for r in repos]


@router.put("/repos/{repo_id}", response_model=RepoConfigResponse)
async def update_repo_endpoint(
    repo_id: UUID,
    body: RepoConfigUpdate,
    _admin: UserResponse = Depends(require_admin),
):
    """Update a repository configuration."""
    repo = await update_repo(repo_id, body)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    return RepoConfigResponse.model_validate(repo)


@router.delete("/repos/{repo_id}")
async def delete_repo_endpoint(
    repo_id: UUID,
    _admin: UserResponse = Depends(require_admin),
):
    """Delete a repository configuration."""
    deleted = await delete_repo(repo_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )
    return {"message": "Repository deleted successfully"}


# ─── User Management ───────────────────────────────────────────────────


@router.get("/users", response_model=list[UserResponse])
async def list_users_endpoint(
    _admin: UserResponse = Depends(require_admin),
):
    """List all users (admin only)."""
    users = await list_users()
    return [UserResponse.model_validate(u) for u in users]


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    body: UserCreate,
    _admin: UserResponse = Depends(require_admin),
):
    """Create a new user (admin only)."""
    user = await create_user(body)
    return UserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user_endpoint(
    user_id: UUID,
    body: UserUpdate,
    _admin: UserResponse = Depends(require_admin),
):
    """Update a user."""
    user = await update_user(user_id, body)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return UserResponse.model_validate(user)


# ─── Permissions ───────────────────────────────────────────────────────


@router.put("/permissions")
async def update_permissions_endpoint(
    body: PermissionsUpdateRequest,
    _admin: UserResponse = Depends(require_admin),
):
    """Update permissions (admin only)."""
    perms = await update_permissions(body.permissions)
    return {
        "message": f"Created {len(perms)} permission(s)",
        "permissions": [
            {
                "id": str(p.id),
                "user_id": str(p.user_id) if p.user_id else None,
                "group_id": str(p.group_id) if p.group_id else None,
                "role_id": str(p.role_id),
                "path_pattern": p.path_pattern,
            }
            for p in perms
        ],
    }
