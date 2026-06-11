from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class TokenPayload(BaseModel):
    sub: str
    exp: int


# User
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=64)
    email: str = Field(..., max_length=128)
    display_name: str = Field(..., max_length=128)
    password: str = Field(..., min_length=6)
    is_superuser: bool = False


class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, max_length=128)
    display_name: Optional[str] = Field(None, max_length=128)
    password: Optional[str] = Field(None, min_length=6)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    display_name: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Role
class RoleResponse(BaseModel):
    id: UUID
    name: str
    is_system: bool

    model_config = {"from_attributes": True}


# Permission
class PermissionCreate(BaseModel):
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    role_id: UUID
    path_pattern: str = Field(..., max_length=256)


class PermissionResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    group_id: Optional[UUID] = None
    role_id: UUID
    path_pattern: str

    model_config = {"from_attributes": True}


class PermissionsUpdateRequest(BaseModel):
    permissions: list[PermissionCreate]


# RepoConfig
class RepoConfigCreate(BaseModel):
    name: str = Field(..., max_length=128)
    git_url: Optional[str] = Field(None, max_length=512)
    local_path: Optional[str] = Field(None, max_length=1024)
    docs_dir: str = "docs"
    ssg_type: str = "vitepress"
    default_branch: str = "main"
    access_token: Optional[str] = None
    commit_template: str = "docs: update {path}"
    review_mode: bool = False
    is_active: bool = True


class RepoConfigUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    git_url: Optional[str] = Field(None, max_length=512)
    local_path: Optional[str] = Field(None, max_length=1024)
    docs_dir: Optional[str] = None
    ssg_type: Optional[str] = None
    default_branch: Optional[str] = None
    access_token: Optional[str] = None
    commit_template: Optional[str] = None
    review_mode: Optional[bool] = None
    is_active: Optional[bool] = None


class RepoConfigResponse(BaseModel):
    id: UUID
    name: str
    git_url: Optional[str] = None
    local_path: Optional[str] = None
    is_local: bool = False
    docs_dir: str
    ssg_type: str
    default_branch: str
    commit_template: str
    review_mode: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# Docs
class FileContentResponse(BaseModel):
    path: str
    content: str
    sha: Optional[str] = None
    encoding: str = "base64"


class SaveFileRequest(BaseModel):
    repo_id: UUID
    path: str
    content: str
    message: Optional[str] = None


class RenameFileRequest(BaseModel):
    repo_id: UUID
    old_path: str
    new_path: str
    message: Optional[str] = None


class TreeItem(BaseModel):
    path: str
    type: str  # "blob" | "tree"
    sha: str
    size: Optional[int] = None


class TreeResponse(BaseModel):
    items: list[TreeItem]


class CommitInfo(BaseModel):
    sha: str
    message: str
    author: str
    date: datetime


class FileHistoryResponse(BaseModel):
    commits: list[CommitInfo]


class DeleteResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
