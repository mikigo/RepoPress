# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (server/)

```bash
cd server
pip install -e .               # Install dependencies
python -m server.cli start      # Start server on http://localhost:8000
python -m server.cli stop       # Stop server (PID-based)
python -m server.cli restart    # Restart server
python -m server.cli createsuperuser  # Interactive superuser creation
```

### Frontend (web/)

```bash
cd web
npm install                     # Install dependencies
npm run dev                     # Dev server on http://localhost:5173 (proxies /api to :8000)
npm run build                   # vue-tsc type-check + vite build
```

## Architecture

**Dual-package monorepo** — `server/` (FastAPI) and `web/` (Vue 3) as independent packages with no build-time coupling. The frontend proxies `/api` to the backend in dev; in production the backend serves the built frontend.

### Data flow

```
Browser → Vue 3 SPA → REST API (FastAPI) → GitHub REST API → Git repository
                          ↓
                    SQLite (users, roles, repo configs only — no doc content)
```

Git is the single source of truth for documentation. The database stores only users, permissions, and repo connection configs (access tokens encrypted with AES-256-CBC).

### Server layers

- `server/config.py` — `pydantic-settings` loading from env vars (`REPOPRESS_` prefix) with sensible defaults
- `server/models.py` — 5 Tortoise-ORM models: User, Role, Permission, UserGroup, RepoConfig. User has M2M to UserGroup.
- `server/schemas.py` — Pydantic v2 request/response schemas with `model_config = {"from_attributes": True}` for ORM mode
- `server/services.py` — Auth (JWT + bcrypt), Admin (repos/users/permissions CRUD), Doc (Git operations via provider), AES token encryption
- `server/repo.py` — `GitProvider` ABC with `GitHubProvider` implementation using `httpx.AsyncClient`. `parse_github_url()` handles HTTPS and SSH formats.
- `server/middleware.py` — ASGI middleware stack: CORS → RateLimit (login: 5/min/IP) → JWT auth → Request logging
- `server/routers/` — 3 route modules: `auth.py` (login/logout/user), `admin.py` (CRUD, admin-only via `require_admin` dep), `docs.py` (file operations)
- `server/cli.py` — argparse CLI: start/stop/restart use PID file at `data/server.pid`

### Server patterns

- Auth dependency chain: `HTTPBearer` → `get_current_user` → `require_admin`. Lower deps use `UserResponse` from Pydantic, not raw ORM objects.
- Tree building: `_build_tree()` in `services.py` converts flat GitHub API tree items into nested `{name, path, type, children}` with dirs-first sorting.
- File save has two modes: `review_mode=False` (direct push to default branch) vs `review_mode=True` (create branch + PR).
- On startup: creates `data/` dirs, initializes DB schemas, seeds default roles (admin/editor/viewer), creates default superuser `admin`/`admin123` if no users exist.

### Frontend layers

- `src/stores.ts` — 4 Pinia stores: auth (JWT in localStorage), editor (current file + dirty tracking), repo (repos + tree), ui (sidebar/preview/theme toggles)
- `src/api.ts` — `ofetch`-based HTTP client with Bearer token auto-attachment and 401→login redirect
- `src/composables.ts` — `useEditor` (file open/save), `usePreview` (markdown-it rendering), `useFileTree` (tree actions + CRUD)
- `src/router.ts` — routes with `meta.auth` and `meta.admin` guards. beforeEach checks authStore state.
- `src/views/` — Login (centered card), Editor (3-panel), Admin pages (DataTable + modal forms)
- `src/components/` — AppHeader (repo selector, save button, user menu), AppSidebar, FileTree (recursive), MarkdownEditor (CodeMirror 6 wrapper), PreviewPanel (markdown-it), Toolbar

### Frontend patterns

- Vue 3 Composition API with `<script setup>` throughout
- Naive UI components used globally (registered in `main.ts`), wrapped in `n-config-provider` for theme support
- CodeMirror 6: modular extensions (markdown, autocompletion, search, history, custom `Ctrl+S` save keymap)
- TypeScript path alias `@/` maps to `src/`
- UnoCSS with `presetUno`, shortcuts for layout classes (`app-layout`, `sidebar`, `preview-panel`)

### Git provider extension

To add a new provider (GitLab, Gitea):
1. Subclass `GitProvider` in `server/repo.py`
2. Implement all 6 abstract methods
3. Add URL parser for the new platform
4. Register in `get_provider_for_repo()` in `services.py`

## Key constraints

- **Min Python 3.10** (lowered from spec's 3.11 for compatibility)
- Database URL is relative: `sqlite://data/repopress.db` — SQLite file is auto-created in `server/data/`
- Access tokens are stored encrypted (AES-256-CBC) in the DB, decrypted only when making API calls
- `auth_mode` config supports `"open"` (skip auth) and `"authenticated"` (default: JWT required)
- Default superuser: `admin` / `admin123` (change in production)
