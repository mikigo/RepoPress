import base64
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
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
