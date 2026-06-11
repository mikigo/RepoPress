import asyncio
import base64
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import httpx


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
class Branch:
    name: str
    sha: str


@dataclass
class PullRequest:
    number: int
    title: str
    url: str
    state: str = "open"


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
    async def create_branch(self, name: str, base: str) -> Branch:
        ...

    @abstractmethod
    async def create_pr(
        self, title: str, head: str, base: str, body: str = ""
    ) -> PullRequest:
        ...

    @abstractmethod
    async def get_file_history(self, path: str) -> list[Commit]:
        ...

    @abstractmethod
    async def get_tree(self, path: str = "", ref: Optional[str] = None) -> list[TreeItem]:
        ...


def parse_github_url(url: str) -> tuple[str, str]:
    """Parse a GitHub URL to extract owner and repo.

    Handles formats:
    - https://github.com/owner/repo.git
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    """
    # HTTPS format
    if "github.com" in url:
        parsed = urlparse(url)
        path = parsed.path.strip("/")
        if path.endswith(".git"):
            path = path[:-4]
        parts = path.split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]

    # SSH format: git@github.com:owner/repo.git
    ssh_match = re.match(r"git@github\.com:([^/]+)/(.+?)\.git$", url)
    if ssh_match:
        return ssh_match.group(1), ssh_match.group(2)

    raise ValueError(f"Unsupported GitHub URL: {url}")


class GitHubProvider(GitProvider):
    """Git provider that uses the GitHub REST API via httpx."""

    API_BASE = "https://api.github.com"

    def __init__(self, git_url: str, access_token: str, default_branch: str = "main"):
        self.owner, self.repo = parse_github_url(git_url)
        self.access_token = access_token
        self.default_branch = default_branch
        self._headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "RepoPress/0.1.0",
        }

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict | list:
        url = f"{self.API_BASE}/repos/{self.owner}/{self.repo}{endpoint}"
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method, url, headers=self._headers, **kwargs
            )
            if response.status_code >= 400:
                detail = response.text
                try:
                    detail = response.json().get("message", detail)
                except Exception:
                    pass
                raise Exception(f"GitHub API error ({response.status_code}): {detail}")
            if response.status_code == 204:
                return {}
            return response.json()

    async def get_file(self, path: str, ref: Optional[str] = None) -> FileInfo:
        ref = ref or self.default_branch
        endpoint = f"/contents/{path}?ref={ref}"
        data = await self._request("GET", endpoint)
        if isinstance(data, list):
            raise FileNotFoundError(f"Path is a directory: {path}")
        content = base64.b64decode(data["content"]).decode("utf-8")
        return FileInfo(
            path=path,
            content=content,
            sha=data.get("sha"),
            encoding="base64",
        )

    async def create_or_update_file(
        self, path: str, content: str, message: str, branch: str
    ) -> CommitResult:
        encoded = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        payload: dict = {
            "message": message,
            "content": encoded,
            "branch": branch,
        }

        # If file exists, get its SHA for update
        try:
            existing = await self.get_file(path, ref=branch)
            payload["sha"] = existing.sha
        except (FileNotFoundError, Exception):
            pass

        data = await self._request("PUT", f"/contents/{path}", json=payload)
        if isinstance(data, dict):
            commit_data = data.get("commit", {})
            return CommitResult(
                sha=commit_data.get("sha", ""),
                url=data.get("content", {}).get("html_url"),
            )
        return CommitResult(sha="")

    async def create_branch(self, name: str, base: str) -> Branch:
        # Get SHA of the base branch
        ref_data = await self._request("GET", f"/git/ref/heads/{base}")
        if isinstance(ref_data, dict):
            sha = ref_data["object"]["sha"]
        else:
            raise Exception("Could not get base branch SHA")

        # Create new branch
        await self._request(
            "POST",
            "/git/refs",
            json={"ref": f"refs/heads/{name}", "sha": sha},
        )
        return Branch(name=name, sha=sha)

    async def create_pr(
        self, title: str, head: str, base: str, body: str = ""
    ) -> PullRequest:
        data = await self._request(
            "POST",
            "/pulls",
            json={"title": title, "head": head, "base": base, "body": body},
        )
        if isinstance(data, dict):
            return PullRequest(
                number=data["number"],
                title=data["title"],
                url=data["html_url"],
                state=data.get("state", "open"),
            )
        raise Exception("Unexpected response creating PR")

    async def get_file_history(self, path: str) -> list[Commit]:
        endpoint = f"/commits?path={path}&sha={self.default_branch}&per_page=30"
        data = await self._request("GET", endpoint)
        if not isinstance(data, list):
            return []
        commits = []
        for item in data:
            commit_data = item.get("commit", {})
            author_data = commit_data.get("author", {}) or {}
            author_name = author_data.get("name", "Unknown")
            date_str = author_data.get("date", "")
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else datetime.now()
            commits.append(
                Commit(
                    sha=item.get("sha", ""),
                    message=commit_data.get("message", ""),
                    author=author_name,
                    date=dt,
                )
            )
        return commits

    async def get_tree(self, path: str = "", ref: Optional[str] = None) -> list[TreeItem]:
        ref = ref or self.default_branch
        if path:
            endpoint = f"/git/trees/{ref}?recursive=1"
        else:
            endpoint = f"/git/trees/{ref}?recursive=1"

        data = await self._request("GET", endpoint)
        if not isinstance(data, dict):
            return []

        tree = data.get("tree", [])
        items = []
        for item in tree:
            item_path = item.get("path", "")
            if path and not item_path.startswith(path):
                continue
            # If filtering by path, strip the prefix
            display_path = item_path[len(path) + 1:] if path and item_path.startswith(path + "/") else item_path
            if path and "/" in display_path and display_path.count("/") > 0:
                # Skip nested items if we're only showing one level
                # Actually, let's include all - the frontend can filter
                pass
            items.append(
                TreeItem(
                    path=item_path,
                    type=item.get("type", "blob"),
                    sha=item.get("sha", ""),
                    size=item.get("size"),
                )
            )
        return items


class LocalGitProvider(GitProvider):
    """Git provider that operates on a local git repository via subprocess."""

    def __init__(self, repo_path: str, default_branch: str = "main"):
        self.repo_path = Path(repo_path).resolve()
        if not (self.repo_path / ".git").exists():
            raise ValueError(f"Not a git repository: {self.repo_path}")
        self.default_branch = default_branch

    async def _run(self, *args: str, cwd: str | None = None) -> str:
        """Run a git command and return stdout."""
        cmd = ["git", "-C", str(cwd or self.repo_path)] + list(args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
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

    async def fetch_and_rebase(self, branch: str) -> dict:
        """Fetch origin and rebase local branch on top. Returns status dict."""
        if not await self._has_remote():
            return {"success": True, "skipped": True, "detail": "No remote configured, skipping fetch"}

        try:
            await self._run("fetch", "origin")
        except Exception as exc:
            return {"success": False, "error": f"Fetch failed: {exc}"}

        if not await self._has_remote_branch(branch):
            return {"success": True, "skipped": True, "detail": "No remote branch yet, skipping rebase"}

        try:
            await self._run("checkout", branch)
            await self._run("pull", "--rebase", "origin", branch)
            return {"success": True, "detail": "Rebase successful"}
        except Exception as exc:
            err = str(exc)
            # Try to abort the rebase if it's in progress
            try:
                await self._run("rebase", "--abort")
            except Exception:
                pass
            return {"success": False, "conflict": True, "error": f"Rebase conflict: {err}"}

    async def push(self, branch: str) -> dict:
        """Push branch to origin. Returns dict with success/error info."""
        if not await self._has_remote():
            return {"success": False, "error": "No remote 'origin' configured"}
        try:
            output = await self._run("push", "origin", branch)
            return {"success": True, "detail": output or "Push successful"}
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def create_branch(self, name: str, base: str) -> Branch:
        await self._run("checkout", base)
        await self._run("checkout", "-b", name)
        sha = await self._run("rev-parse", "HEAD")
        return Branch(name=name, sha=sha)

    async def create_pr(
        self, title: str, head: str, base: str, body: str = ""
    ) -> PullRequest:
        raise NotImplementedError("PR creation not supported for local repos")

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
