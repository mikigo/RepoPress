from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from server.routers.auth import get_current_user
from server.schemas import (
    DeleteResponse,
    FileContentResponse,
    FileHistoryResponse,
    RenameFileRequest,
    SaveFileRequest,
    UserResponse,
)
from server.services import (
    delete_file as svc_delete_file,
    get_file as svc_get_file,
    get_file_history as svc_get_file_history,
    get_tree as svc_get_tree,
    rename_file as svc_rename_file,
    save_file as svc_save_file,
)

router = APIRouter(prefix="/api/docs", tags=["docs"])


@router.get("/tree", response_model=list[dict])
async def get_tree(
    repo_id: UUID = Query(..., description="Repository ID"),
    path: str = Query("", description="Path to list"),
    ref: str = Query(None, description="Git ref (branch/commit)"),
    _user: UserResponse = Depends(get_current_user),
):
    """Get the file tree for a repository."""
    try:
        items = await svc_get_tree(repo_id, path=path, ref=ref)
        return items
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/{path:path}", response_model=FileContentResponse)
async def get_file(
    path: str,
    repo_id: UUID = Query(..., description="Repository ID"),
    ref: str = Query(None, description="Git ref (branch/commit)"),
    _user: UserResponse = Depends(get_current_user),
):
    """Get the content of a file."""
    try:
        content = await svc_get_file(repo_id, path, ref=ref)
        return content
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/save")
async def save_file(
    body: SaveFileRequest,
    _user: UserResponse = Depends(get_current_user),
):
    """Save (create or update) a file."""
    try:
        result = await svc_save_file(
            repo_id=body.repo_id,
            path=body.path,
            content=body.content,
            message=body.message,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.delete("/{path:path}", response_model=DeleteResponse)
async def delete_file(
    path: str,
    repo_id: UUID = Query(..., description="Repository ID"),
    message: str = Query(None, description="Commit message"),
    _user: UserResponse = Depends(get_current_user),
):
    """Delete a file."""
    try:
        result = await svc_delete_file(repo_id, path, message=message)
        return result
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.post("/rename")
async def rename_file(
    body: RenameFileRequest,
    _user: UserResponse = Depends(get_current_user),
):
    """Rename a file."""
    try:
        result = await svc_rename_file(
            repo_id=body.repo_id,
            old_path=body.old_path,
            new_path=body.new_path,
            message=body.message,
        )
        return result
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )


@router.get("/{path:path}/history", response_model=list[dict])
async def get_file_history(
    path: str,
    repo_id: UUID = Query(..., description="Repository ID"),
    _user: UserResponse = Depends(get_current_user),
):
    """Get the commit history for a file."""
    try:
        history = await svc_get_file_history(repo_id, path)
        return history
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )
