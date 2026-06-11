import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from tortoise.exceptions import DoesNotExist

from config import settings
from models import Permission, RepoConfig, Role, User
from repo import GitHubProvider, GitProvider, LocalGitProvider
from schemas import (
    FileContentResponse,
    PermissionCreate,
    RepoConfigCreate,
    RepoConfigUpdate,
    UserCreate,
    UserUpdate,
)

logger = logging.getLogger("repopress")


# ─── Encryption helpers for access_token ───────────────────────────────
def _pad_key(key: str) -> bytes:
    """Ensure key is exactly 32 bytes for AES-256."""
    key_bytes = key.encode("utf-8")
    if len(key_bytes) >= 32:
        return key_bytes[:32]
    return key_bytes.ljust(32, b"\0")


def encrypt_token(plaintext: str, key: str = settings.encryption_key) -> str:
    """Encrypt a plaintext string using AES-256-CBC and return base64."""
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    key_bytes = _pad_key(key)
    iv = base64.b64decode("AAAAAAAAAAAAAAAAAAAAAA==")  # 16 zero bytes for simplicity
    # In production use os.urandom(16) and store the IV alongside
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded_data) + encryptor.finalize()
    return base64.b64encode(encrypted).decode("utf-8")


def decrypt_token(ciphertext_b64: str, key: str = settings.encryption_key) -> str:
    """Decrypt a base64 AES-256-CBC encrypted string."""
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    key_bytes = _pad_key(key)
    iv = base64.b64decode("AAAAAAAAAAAAAAAAAAAAAA==")
    cipher = Cipher(algorithms.AES(key_bytes), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(base64.b64decode(ciphertext_b64)) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded_data) + unpadder.finalize()).decode("utf-8")


# ─── Auth Service ──────────────────────────────────────────────────────

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(user: User) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {
        "sub": str(user.id),
        "username": user.username,
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


async def create_user(user_data: UserCreate) -> User:
    hashed = get_password_hash(user_data.password)
    user = await User.create(
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        hashed_password=hashed,
        is_superuser=user_data.is_superuser,
    )
    return user


async def authenticate_user(username: str, password: str) -> Optional[User]:
    try:
        user = await User.get(username=username)
    except DoesNotExist:
        return None
    if not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_user_by_id(user_id: UUID) -> Optional[User]:
    try:
        return await User.get(id=user_id)
    except DoesNotExist:
        return None


# ─── Admin Service ─────────────────────────────────────────────────────

async def create_repo(repo_data: RepoConfigCreate) -> RepoConfig:
    encrypted_token = encrypt_token(repo_data.access_token) if repo_data.access_token else ""
    repo = await RepoConfig.create(
        name=repo_data.name,
        git_url=repo_data.git_url,
        local_path=repo_data.local_path,
        docs_dir=repo_data.docs_dir,
        ssg_type=repo_data.ssg_type,
        default_branch=repo_data.default_branch,
        access_token=encrypted_token,
        commit_template=repo_data.commit_template,
        review_mode=repo_data.review_mode,
        is_active=repo_data.is_active,
    )
    return repo


async def get_repos() -> list[RepoConfig]:
    return await RepoConfig.all().order_by("-created_at")


async def get_repo_by_id(repo_id: UUID) -> Optional[RepoConfig]:
    try:
        return await RepoConfig.get(id=repo_id)
    except DoesNotExist:
        return None


async def update_repo(repo_id: UUID, repo_data: RepoConfigUpdate) -> Optional[RepoConfig]:
    repo = await get_repo_by_id(repo_id)
    if not repo:
        return None

    update_fields = repo_data.model_dump(exclude_unset=True)
    if "access_token" in update_fields and update_fields["access_token"]:
        update_fields["access_token"] = encrypt_token(update_fields["access_token"])

    if update_fields:
        await RepoConfig.filter(id=repo_id).update(**update_fields)

    return await get_repo_by_id(repo_id)


async def delete_repo(repo_id: UUID) -> bool:
    count = await RepoConfig.filter(id=repo_id).delete()
    return count > 0


async def list_users() -> list[User]:
    return await User.all().order_by("-created_at")


async def update_user(user_id: UUID, user_data: UserUpdate) -> Optional[User]:
    user = await get_user_by_id(user_id)
    if not user:
        return None

    update_fields = user_data.model_dump(exclude_unset=True)
    if "password" in update_fields and update_fields["password"]:
        update_fields["hashed_password"] = get_password_hash(update_fields.pop("password"))

    if update_fields:
        await User.filter(id=user_id).update(**update_fields)

    return await get_user_by_id(user_id)


async def update_permissions(permissions: list[PermissionCreate]) -> list[Permission]:
    created = []
    for perm_data in permissions:
        perm = await Permission.create(
            user_id=perm_data.user_id,
            group_id=perm_data.group_id,
            role_id=perm_data.role_id,
            path_pattern=perm_data.path_pattern,
        )
        created.append(perm)
    return created


async def get_user_permissions(user_id: UUID) -> list[Permission]:
    """Get all permissions for a user (direct + group-based)."""
    user = await get_user_by_id(user_id)
    if not user:
        return []

    # Direct permissions
    direct = await Permission.filter(user_id=user_id).prefetch_related("role")

    # Group-based permissions
    groups = await user.groups.all()
    group_ids = [g.id for g in groups]
    group_perms = await Permission.filter(group_id__in=group_ids).prefetch_related("role") if group_ids else []

    return direct + group_perms


# ─── Doc Service ───────────────────────────────────────────────────────

async def get_provider_for_repo(repo_id: UUID) -> GitProvider:
    """Get a configured GitProvider for a given repo config."""
    repo = await get_repo_by_id(repo_id)
    if not repo:
        raise ValueError(f"Repo not found: {repo_id}")

    if repo.local_path:
        return LocalGitProvider(
            repo_path=repo.local_path,
            default_branch=repo.default_branch,
        )

    token = decrypt_token(repo.access_token)
    return GitHubProvider(
        git_url=repo.git_url,
        access_token=token,
        default_branch=repo.default_branch,
    )


async def get_file(repo_id: UUID, path: str, ref: Optional[str] = None) -> FileContentResponse:
    provider = await get_provider_for_repo(repo_id)
    repo = await get_repo_by_id(repo_id)
    if not repo:
        raise ValueError("Repo not found")

    file_info = await provider.get_file(path, ref=ref or repo.default_branch)
    return FileContentResponse(
        path=file_info.path,
        content=file_info.content,
        sha=file_info.sha,
        encoding=file_info.encoding,
    )


async def save_file(
    repo_id: UUID, path: str, content: str, message: Optional[str] = None
) -> dict:
    repo = await get_repo_by_id(repo_id)
    if not repo:
        raise ValueError("Repo not found")

    provider = await get_provider_for_repo(repo_id)
    commit_msg = message or repo.commit_template.format(path=path)

    if repo.review_mode:
        # PR mode: create a branch, commit, and open PR
        branch_name = f"docs/update-{path.replace('/', '-').replace('.', '-')}"
        try:
            await provider.create_branch(branch_name, repo.default_branch)
        except Exception as exc:
            # Branch may already exist; try to reuse
            logger.warning("Branch creation (may already exist): %s", exc)

        result = await provider.create_or_update_file(
            path=path, content=content, message=commit_msg, branch=branch_name
        )
        pr = await provider.create_pr(
            title=commit_msg,
            head=branch_name,
            base=repo.default_branch,
            body=f"Documentation update for {path}",
        )
        return {
            "commit_sha": result.sha,
            "pr_number": pr.number,
            "pr_url": pr.url,
            "mode": "review",
        }
    else:
        # Direct mode: fetch → rebase → write → commit → push
        rebase_result = None
        push_result = None

        if isinstance(provider, LocalGitProvider):
            rebase_result = await provider.fetch_and_rebase(repo.default_branch)
            if not rebase_result.get("success"):
                return {
                    "mode": "direct",
                    "rebase": rebase_result,
                    "conflict": rebase_result.get("conflict", False),
                }

        result = await provider.create_or_update_file(
            path=path, content=content, message=commit_msg, branch=repo.default_branch
        )

        if isinstance(provider, LocalGitProvider):
            push_result = await provider.push(repo.default_branch)

        return {
            "commit_sha": result.sha,
            "mode": "direct",
            "rebase": rebase_result,
            "push": push_result,
        }


async def delete_file(repo_id: UUID, path: str, message: Optional[str] = None) -> dict:
    repo = await get_repo_by_id(repo_id)
    if not repo:
        raise ValueError("Repo not found")

    provider = await get_provider_for_repo(repo_id)
    commit_msg = message or f"docs: delete {path}"

    encoded = base64.b64encode(b"").decode("utf-8")
    try:
        file_info = await provider.get_file(path, ref=repo.default_branch)
    except (FileNotFoundError, Exception) as exc:
        raise ValueError(f"File not found: {path}") from exc

    endpoint = f"/contents/{path}"
    payload = {
        "message": commit_msg,
        "sha": file_info.sha,
        "branch": repo.default_branch,
    }

    import httpx
    headers = {
        "Authorization": f"Bearer {decrypt_token(repo.access_token)}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "RepoPress/0.1.0",
    }
    from repo import parse_github_url
    owner, repo_name = parse_github_url(repo.git_url)
    url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"

    async with httpx.AsyncClient() as client:
        response = await client.request("DELETE", url, headers=headers, json=payload)
        if response.status_code >= 400:
            detail = response.text
            try:
                detail = response.json().get("message", detail)
            except Exception:
                pass
            raise Exception(f"GitHub API error: {detail}")

    return {"message": f"Deleted {path}"}


async def rename_file(
    repo_id: UUID, old_path: str, new_path: str, message: Optional[str] = None
) -> dict:
    """Rename a file by reading old content and writing to new path."""
    # Read old content
    file_response = await get_file(repo_id, old_path)
    content = file_response.content

    # Save to new path
    result = await save_file(repo_id, new_path, content, message)

    # Delete old file
    delete_msg = message or f"docs: rename {old_path} to {new_path}"
    await delete_file(repo_id, old_path, delete_msg)

    return {
        **result,
        "old_path": old_path,
        "new_path": new_path,
    }


def _add_nested(parent: dict, item, relative_path: str):
    """Recursively add an item into the tree at the correct depth."""
    parts = relative_path.split("/", 1)

    if len(parts) == 1:
        # Direct child of parent
        full_child = {
            "name": parts[0],
            "path": item.path,
            "type": "file" if item.type == "blob" else "dir",
            "children": [] if item.type == "tree" else None,
        }
        if full_child not in parent["children"]:
            parent["children"].append(full_child)
    else:
        dir_name, rest = parts
        dir_path = parent["path"] + "/" + dir_name
        # Find or create intermediate dir
        child_dir = next(
            (c for c in parent["children"] if c["name"] == dir_name and c["type"] == "dir"),
            None,
        )
        if child_dir is None:
            child_dir = {
                "name": dir_name,
                "path": dir_path,
                "type": "dir",
                "children": [],
            }
            parent["children"].append(child_dir)
        _add_nested(child_dir, item, rest)


def _build_tree(items: list, prefix: str = "") -> list[dict]:
    """Build a nested tree structure from flat path items."""
    tree_map: dict[str, dict] = {}

    for item in items:
        item_path = item.path
        if prefix and not item_path.startswith(prefix + "/"):
            continue

        relative = item_path[len(prefix) + 1:] if prefix else item_path
        parts = relative.split("/")

        if len(parts) == 1:
            # Direct child of prefix
            name = parts[0]
            tree_map[name] = {
                "name": name,
                "path": item_path,
                "type": "file" if item.type == "blob" else "dir",
                "children": [] if item.type == "tree" else None,
            }
        else:
            # Nested — ensure parent dir exists, then recurse
            dir_name = parts[0]
            if dir_name not in tree_map:
                dir_path = prefix + "/" + dir_name if prefix else dir_name
                tree_map[dir_name] = {
                    "name": dir_name,
                    "path": dir_path,
                    "type": "dir",
                    "children": [],
                }
            _add_nested(tree_map[dir_name], item, "/".join(parts[1:]))

    # Sort: dirs first, then alphabetical
    result = sorted(tree_map.values(), key=lambda x: (0 if x["type"] == "dir" else 1, x["name"]))
    for item in result:
        if item.get("children"):
            item["children"] = sorted(item["children"],
                key=lambda x: (0 if x["type"] == "dir" else 1, x["name"]))

    return result


async def get_tree(repo_id: UUID, path: str = "", ref: Optional[str] = None) -> list:
    provider = await get_provider_for_repo(repo_id)
    repo = await get_repo_by_id(repo_id)
    if not repo:
        raise ValueError("Repo not found")

    items = await provider.get_tree(path=path, ref=ref or repo.default_branch)

    # Get all items from repo if we need to filter by docs_dir
    if repo.docs_dir and not path:
        # Fetch the full recursive tree and filter to docs_dir
        all_items = await provider.get_tree(path="", ref=ref or repo.default_branch)
        docs_prefix = repo.docs_dir.strip("/")
        filtered = [i for i in all_items if i.path.startswith(docs_prefix + "/") or i.path == docs_prefix]
        return _build_tree(filtered, docs_prefix)
    elif path:
        return _build_tree(items, path)
    else:
        return _build_tree(items, "")


async def get_file_history(repo_id: UUID, path: str) -> list:
    provider = await get_provider_for_repo(repo_id)
    commits = await provider.get_file_history(path)
    return [
        {
            "sha": c.sha,
            "message": c.message,
            "author": c.author,
            "date": c.date.isoformat(),
        }
        for c in commits
    ]
