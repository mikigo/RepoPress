# RepoPress

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

> Git-based CMS for documentation sites. Edit Markdown/MDX online with live preview, commit and push directly to your docs repository.
>
> 基于 Git 的文档 CMS。在线编辑 Markdown/MDX，实时预览，提交并推送到文档仓库。

RepoPress 在 Git 仓库和静态文档站之间搭一层 CMS。连接仓库后，在线编辑 Markdown/MDX、实时预览、提交推送——不改动原有的 VitePress / Rspress / Docusaurus / MkDocs Material 项目。

------

## Quick Start

```bash
# 后端
cd server
pip install -e .
python -m server.cli createsuperuser    # 创建管理员（默认 admin/admin123）
python -m server.cli start              # 启动 → http://localhost:8000

# 前端
cd web
npm install
npm run dev                             # 启动 → http://localhost:5173
```

打开 `http://localhost:5173`，用管理员账户登录。进入管理后台添加仓库：

**远程仓库（GitHub）：**

```
Git URL  → https://github.com/team/docs.git
Docs 目录 → docs/
SSG 类型  → rspress
Access Token → ghp_xxx
```

**本地仓库（无需 Token）：**

```
Name       → My Docs
Local Path → /path/to/local/repo
Docs 目录   → docs/
SSG 类型    → rspress
```

添加后，切换至编辑器即可浏览文件树、在线编辑。支持多仓库独立配置。

### docs 端集成

在 SSG 配置中将 `editLink` 指向 RepoPress 编辑器，文档页即出现编辑按钮。

**Rspress** — `rspress.config.ts`

```typescript
export default defineConfig({
  themeConfig: {
    editLink: {
      docRepoBaseUrl: 'https://repopress.example.com/editor/<repo-id>/docs'
    }
  }
})
```

<details>
<summary>其他 SSG</summary>

**VitePress** — `.vitepress/config.ts`

```typescript
export default defineConfig({
  themeConfig: {
    editLink: {
      pattern: 'https://repopress.example.com/editor/<repo-id>/docs/:path'
    }
  }
})
```

**Docusaurus** — `docusaurus.config.js`

```javascript
module.exports = {
  presets: [['classic', {
    docs: { editUrl: 'https://repopress.example.com/editor/<repo-id>/docs/' }
  }]]
}
```

**MkDocs Material** — `mkdocs.yml`

```yaml
edit_uri: https://repopress.example.com/editor/<repo-id>/docs/
```

</details>

------

## 解决的痛点

非开发人员改文档要走 Git CLI + PR 流程，学习成本高。RepoPress 用在线编辑替代：

**之前**：发现错误 → Clone 仓库 → 本地编辑 → Commit → Push → Create PR → Code Review → Merge

**之后**：发现错误 → 在线编辑 → 保存 → 完成

核心原则：**Git 是唯一数据源**。RepoPress 不存文档内容——文档始终在用户的 Git 仓库里，服务端数据库只管用户、权限和系统配置。

------

## 功能

**在线编辑** — CodeMirror 6 驱动的 Markdown/MDX 编辑器。语法高亮、自动补全、格式化工具栏（加粗/斜体/标题/链接/图片/代码块/列表/引用）、`Ctrl+S` 保存。

**文件管理** — 侧边栏文件树，支持展开/收起（状态持久化到 localStorage）。单击文件打开编辑，单击目录展开。顶部 **+** 按钮新建文件（自动识别选中目录），**−** 按钮删除文件（含确认弹窗）。

**实时预览** — 右分屏 Markdown 渲染预览，编辑即时刷新。支持编号列表、代码块、表格、引用等 Markdown 元素。预览面板可切换显隐。

**保存流程** — 保存前弹出确认弹窗，确认后执行 `pull --rebase → 写文件 → commit → push`。有冲突时中止并提示。本地仓库模式下自动 git commit + push，远程仓库通过 GitHub API。

**面板可拖拽** — 文件树、编辑区、预览区之间可拖动分隔条调整宽度。编辑区和预览区滚动同步。

**权限管理** — RBAC 三级角色（Admin / Editor / Viewer），权限可细化到目录。支持用户组。鉴权模式可选：`authenticated` 需登录后按角色控制。

**编辑器状态持久化** — 刷新页面后恢复上次打开的文件和编辑内容。

------

## 架构

### 系统架构

```
Browser → Vue 3 SPA → REST API (FastAPI) → Git Repository (local or GitHub API)
                       ↓
                 SQLite (users, roles, repo configs only — no doc content)
```

### 项目结构

```
repopress/
├── server/   — FastAPI 后端
│   ├── cli.py        # start / stop / restart / createsuperuser
│   ├── main.py       # FastAPI 入口 + 生命周期
│   ├── config.py     # pydantic-settings 配置
│   ├── middleware.py  # CORS / JWT / RateLimit / Logging
│   ├── models.py     # Tortoise-ORM 模型
│   ├── schemas.py    # Pydantic v2 请求/响应
│   ├── services.py   # 业务逻辑（Auth / Admin / Doc / Tree）
│   ├── repo.py       # GitProvider ABC + GitHub + Local 实现
│   └── routers/      # auth / admin / docs 路由
└── web/      — Vue 3 前端
    └── src/
        ├── main.ts        # 入口
        ├── App.vue        # 根组件
        ├── router.ts      # 路由 + 守卫
        ├── stores.ts      # Pinia stores
        ├── api.ts         # ofetch 客户端
        ├── composables.ts # useEditor / usePreview / useFileTree
        ├── views/         # Login / Editor / Admin*
        ├── components/    # Header / Sidebar / FileTree / MarkdownEditor / PreviewPanel / Toolbar
        └── styles/        # 全局样式 + markdown-preview
```

### 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router 4 |
| 编辑器 | CodeMirror 6 + markdown-it |
| UI | Naive UI + UnoCSS |
| HTTP | ofetch |
| 后端 | FastAPI + Tortoise-ORM + Pydantic v2 |
| 数据库 | SQLite |
| Git | asyncio subprocess (本地) / httpx (GitHub API) |
| 认证 | JWT + bcrypt |

------

## 配置

所有配置通过 `config.py` 的 `Settings` 类管理，环境变量前缀 `REPOPRESS_`：

```python
# 服务
host: str = "0.0.0.0"
port: int = 8000
debug: bool = False

# 数据库
database_url: str = "sqlite://data/repopress.db"

# 认证
auth_mode: str = "authenticated"   # "authenticated" | "open"
jwt_secret: str                    # 生产环境务必修改
jwt_algorithm: str = "HS256"
jwt_expire_minutes: int = 1440     # 24 小时

# Git
git_clone_dir: str = "data/repos"
encryption_key: str                # AES-256-CBC，用于加密 Access Token
```

- `auth_mode = "authenticated"`：需登录，按角色和目录权限控制
- `auth_mode = "open"`：跳过登录

### 命令行

```bash
python -m server.cli start              # 启动服务器
python -m server.cli stop               # 停止服务器（PID 文件）
python -m server.cli restart            # 重启
python -m server.cli createsuperuser    # 交互式创建管理员
```

### 默认超管

首次启动自动创建：`admin` / `admin123`（生产环境务必修改）。

------

## Git Provider

RepoPress 支持两种 Provider：

### LocalGitProvider

直接操作本地 Git 仓库，通过 `asyncio.subprocess` 执行 git 命令：

- 读取：`git show <ref>:<path>`
- 写入：写文件 → `git add` → `git commit`
- 保存流程：`git checkout` → `git pull --rebase origin <branch>` → 写文件 → `git add + commit` → `git push`
- 冲突检测：rebase 失败自动 `git rebase --abort`，返回冲突提示
- 使用场景：本地开发、局域网部署

### GitHubProvider

通过 GitHub REST API 操作远程仓库（httpx 异步客户端）：

- 读取：`GET /repos/{owner}/{repo}/contents/{path}`
- 写入：`PUT /repos/{owner}/{repo}/contents/{path}`
- 分支 + PR：创建分支、提交、创建 Pull Request
- 使用场景：托管在 GitHub 的文档仓库

### 扩展

实现 `GitProvider` 抽象基类的 6 个方法即可添加新平台（GitLab、Gitea 等）。

------

## API

### `/api/docs/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/docs/{path}` | 获取文件内容 |
| POST | `/api/docs/save` | 创建/更新文件 |
| DELETE | `/api/docs/{path}` | 删除文件 |
| POST | `/api/docs/rename` | 重命名/移动 |
| GET | `/api/docs/{path}/history` | 文件历史 |
| GET | `/api/docs/tree` | 文件目录树 |

### `/api/auth/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/user` | 当前用户 |

### `/api/admin/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/admin/repos` | 仓库列表 |
| POST | `/api/admin/repos` | 添加仓库 |
| PUT | `/api/admin/repos/{id}` | 更新仓库 |
| DELETE | `/api/admin/repos/{id}` | 删除仓库 |
| GET | `/api/admin/users` | 用户列表 |
| POST | `/api/admin/users` | 创建用户 |
| PUT | `/api/admin/users/{id}` | 更新用户 |
| GET | `/api/admin/permissions` | 权限列表 |
| PUT | `/api/admin/permissions` | 更新权限 |

------

## License

[Apache 2.0](LICENSE)
