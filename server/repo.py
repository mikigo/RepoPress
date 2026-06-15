from __future__ import annotations
import asyncio
import base64
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    path: str
    content: str
    sha: Optional[str] = None
    encoding: str = "base64"


@dataclass
class CommitResult:
    sha: str
    url: Optional[str] = None


@dataclass
class TreeItem:
    path: str
    type: str  # "blob" | "tree"
    sha: str
    size: Optional[int] = None


@dataclass
class Commit:
    sha: str
    message: str
    author: str
    date: datetime


class GitProvider(ABC):
    """Abstract base for Git operations."""

    @abstractmethod
    async def get_file(self, path: str, ref: Optional[str] = None) -> FileInfo:
        ...

    @abstractmethod
    async def create_or_update_file(
        self, path: str, content: str, message: str, branch: str
    ) -> CommitResult:
        ...

    @abstractmethod
    async def get_file_history(self, path: str) -> list[Commit]:
        ...

    @abstractmethod
    async def get_tree(self, path: str = "", ref: Optional[str] = None) -> list[TreeItem]:
        ...


class LocalGitProvider(GitProvider):
    """Git provider that operates on a local git repository via subprocess."""

    def __init__(self, repo_path: str, default_branch: str = "main"):
        self.repo_path = Path(repo_path).resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
        self.default_branch = default_branch

    async def _run(self, *args: str, cwd: str | None = None, timeout: int = 30) -> str:
        """Run a git command and return stdout."""
        cmd = ["git", "-C", str(cwd or self.repo_path)] + list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise Exception(f"git {args[0]} timed out after {timeout}s")
        if proc.returncode != 0:
            err = stderr.decode().strip()
            raise Exception(f"git {args[0]} failed: {err}")
        return stdout.decode().strip()

    async def get_file(self, path: str, ref: Optional[str] = None) -> FileInfo:
        ref = ref or self.default_branch
        content = await self._run("show", f"{ref}:{path}")
        sha = await self._run("rev-parse", f"{ref}:{path}")
        return FileInfo(
            path=path,
            content=content,
            sha=sha,
            encoding="utf-8",
        )

    async def create_or_update_file(
        self, path: str, content: str, message: str, branch: str
    ) -> CommitResult:
        full_path = self.repo_path / path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")

        # Checkout target branch
        await self._run("checkout", branch)

        await self._run("add", path)
        await self._run("commit", "-m", message, "--allow-empty")
        sha = await self._run("rev-parse", "HEAD")
        return CommitResult(sha=sha, url=None)

    async def _has_remote(self) -> bool:
        """Check if origin remote is configured."""
        try:
            remotes = await self._run("remote")
            return "origin" in remotes
        except Exception:
            return False

    async def _has_remote_branch(self, branch: str) -> bool:
        """Check if remote tracking branch exists."""
        try:
            await self._run("rev-parse", "--verify", f"origin/{branch}")
            return True
        except Exception:
            return False

    async def _is_working_tree_clean(self) -> bool:
        """Check if working directory has no modified tracked files."""
        try:
            status = await self._run("status", "--porcelain")
            for line in status.splitlines():
                if line.strip():
                    # Ignore untracked files only (lines starting with ??)
                    if not line.startswith("??"):
                        return False
            return True
        except Exception:
            return False

    async def _stash_changes(self) -> Optional[str]:
        """Stash local changes. Returns stash ref if stashed, None if nothing to stash."""
        try:
            output = await self._run("stash", "push", "-m", "repopress-autostash")
            if "No local changes to save" in output:
                return None
            return "stash@{0}"
        except Exception:
            return None

    async def _stash_pop(self) -> dict:
        """Pop the most recent stash. Returns success/conflict info."""
        try:
            await self._run("stash", "pop")
            return {"success": True, "detail": "Stash pop successful"}
        except Exception as exc:
            err = str(exc)
            # Check if it's a merge conflict during stash pop
            if "CONFLICT" in err or "conflict" in err.lower():
                return {"success": False, "conflict": True,
                        "error": f"Stash pop conflict: {err}"}
            return {"success": False, "conflict": False,
                    "error": f"Stash pop failed: {err}"}

    async def fetch_and_rebase(self, branch: str) -> dict:
        """Pull with rebase. Auto-stashes local changes to ensure clean working tree.
        Returns status dict. Fast-path: skips if no remote or no remote branch."""
        if not await self._has_remote():
            return {"success": True, "skipped": True, "detail": "No remote configured, skipping fetch"}

        # Checkout to the target branch first
        await self._run("checkout", branch)

        if not await self._has_remote_branch(branch):
            return {"success": True, "skipped": True, "detail": "No remote branch yet, skipping rebase"}

        stash_ref = None
        if not await self._is_working_tree_clean():
            stash_ref = await self._stash_changes()

        try:
            await self._run("pull", "--rebase", "origin", branch)
        except Exception as exc:
            err = str(exc)
            try:
                await self._run("rebase", "--abort")
            except Exception:
                pass
            # Pop stash before returning error
            if stash_ref:
                await self._stash_pop()
            return {"success": False, "conflict": True, "error": f"Rebase conflict: {err}"}

        rebase_result = {"success": True, "detail": "Rebase successful"}
        stash_result = None

        if stash_ref:
            stash_result = await self._stash_pop()
            if not stash_result.get("success"):
                # Stash pop conflict: real conflict (remote changes vs local uncommitted)
                rebase_result = {"success": False, "conflict": True,
                                 "error": stash_result.get("error", "Merge conflict after rebase")}

        if stash_result:
            rebase_result["stash"] = stash_result

        return rebase_result

    async def delete_file(self, path: str, message: str, branch: str):
        """Delete a file and commit the deletion."""
        await self._run("checkout", branch)
        await self._run("rm", path)
        await self._run("commit", "-m", message, "--allow-empty")

    async def push(self, branch: str) -> dict:
        """Push branch to origin. Returns dict with success/error info."""
        if not await self._has_remote():
            return {"success": False, "error": "No remote 'origin' configured"}
        try:
            output = await self._run("push", "origin", branch)
            return {"success": True, "detail": output or "Push successful"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def get_file_history(self, path: str) -> list[Commit]:
        fmt = "--format=%H||%s||%an||%aI"
        output = await self._run("log", fmt, "--", path)
        commits = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            parts = line.split("||", 3)
            if len(parts) == 4:
                commits.append(Commit(
                    sha=parts[0],
                    message=parts[1],
                    author=parts[2],
                    date=datetime.fromisoformat(parts[3]),
                ))
        return commits

    async def get_tree(self, path: str = "", ref: Optional[str] = None) -> list[TreeItem]:
        ref = ref or self.default_branch
        prefix = f"{ref}:{path}" if path else ref
        output = await self._run("ls-tree", "-r", prefix)
        items = []
        for line in output.split("\n"):
            if not line.strip():
                continue
            # format: <mode> <type> <sha>\t<path>
            meta, file_path = line.split("\t", 1)
            mode, obj_type, sha = meta.split()
            full_path = f"{path}/{file_path}" if path else file_path
            items.append(TreeItem(
                path=full_path,
                type=obj_type,
                sha=sha,
                size=None,
            ))
        return items
