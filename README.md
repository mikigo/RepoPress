# RepoPress

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

> Git-based CMS for documentation sites. Edit Markdown/MDX in the browser with live preview. Save commits directly to your docs repository — no Git CLI required.
>
> 基于 Git 的文档 CMS。在线编辑 Markdown/MDX，实时预览，提交推送到文档仓库。零 Git 门槛。

RepoPress 是文档站点和 Git 仓库之间的一层 CMS。连接仓库后即可在线编辑文档，实时预览效果，保存后自动提交推送。不改动原有的 VitePress / Rspress / Docusaurus / MkDocs Material 项目结构和构建流程。

**核心原则：Git 是唯一数据源。** RepoPress 不存储文档内容——文档始终在你的 Git 仓库里，服务端数据库仅管理用户、权限和仓库连接配置。

---

## 快速上手

### 1. 启动服务

```bash
# 后端
cd server
pip install -e .
python -m server.cli start              # http://0.0.0.0:8000

# 前端
cd web
npm install
npm run build                           # 生产构建
```

### 2. 部署

**开发环境**：前端 `npm run dev`，后端 `python -m server.cli start`。开发服务器自带热更新。

**生产环境**：前端 `npm run build` 输出至 `web/dist/`，后端 `server/static/` 自动包含构建产物。使用 Nginx 反向代理：

```nginx
server {
    listen 80;
    server_name repopress.example.com;

    # 前端 SPA + 静态资源
    location / {
        proxy_pass http://127.0.0.1:8000;
    }

    # API 直接透传
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 3. 创建管理员

```bash
cd server
python -m server.cli createsuperuser
```

首次启动时如果没有用户，会自动创建默认管理员 `admin` / `admin123`（生产环境务必修改）。

### 4. 添加文档仓库

访问 `http://10.0.21.144:8000`，用管理员账户登录。点击右上角用户名 → **Setting**，在仓库管理中添加仓库：

| 字段 | 值 | 说明 |
|------|-----|------|
| Name | My Docs | 仓库显示名称 |
| Local Path | `/home/pz/sailwind_docs` | 文档项目的本地路径 |
| Docs 目录 | `docs` | 文档内容所在的子目录 |
| SSG 类型 | `rspress` | 静态站点生成器类型 |

保存后在仓库列表中会显示 **Repo ID**（UUID 格式），点击 📋 按钮复制。这个 ID 用于下一步配置 editLink。

支持多仓库独立配置，每个仓库有独立的文件树和编辑环境。

---

## 接入文档站点

以 Rspress 为例。VitePress / Docusaurus / MkDocs Material 同理——在对应配置中设置 editLink 即可。

### Step 1: 复制 EditLink 组件

将 RepoPress 提供的 EditLink 组件复制到 Rspress 项目的 theme 目录：

```bash
mkdir -p theme/components/EditLink
cp integrations/rspress/EditLink.tsx theme/components/EditLink/index.tsx
```

> 这个组件替代 Rspress 默认的编辑链接行为，确保所有编辑按钮在同一个浏览器窗口中打开，避免多开标签页。

### Step 2: 注册组件

编辑 `theme/index.tsx`（如不存在则创建）：

```tsx
import './index.css';
import { Layout } from '@rspress/core/theme-original';
import { EditLink } from './components/EditLink';

export { Layout, EditLink };
export * from '@rspress/core/theme-original';
```

### Step 3: 配置 editLink

在 `rspress.config.ts` 的 `themeConfig` 中添加：

```typescript
export default defineConfig({
    themeConfig: {
        editLink: {
            docRepoBaseUrl: 'https://repopress.example.com/editor/<repo-id>/docs',
        },
    },
});
```

将 `<repo-id>` 替换为 RepoPress 管理后台中仓库对应的 ID。

### Step 4: 验证

重启 Rspress 开发服务器，打开任意文档页面。页面底部和右侧大纲栏应出现"编辑此页面"链接。点击后跳转到 RepoPress 编辑器，在线编辑、Ctrl+S 保存、自动提交推送。

---

<details>
<summary>其他 SSG 配置</summary>

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

---

## 核心功能

**在线编辑** — CodeMirror 6 驱动的 Markdown/MDX 编辑器。语法高亮、自动补全、格式化工具栏（加粗/斜体/标题/链接/图片/代码块/列表/引用），`Ctrl+S` 保存。

**文件管理** — 侧边栏文件树，支持展开/收起、新建/删除文件/目录。可按文件后缀配置隐藏特定格式（`.pdf, .png, .zip` 等）。

**实时预览** — 右分屏 Markdown 渲染，编辑即时刷新。支持编号列表、代码块、表格、引用等元素。预览面板可切换显隐。

**保存流程** — 确认弹窗 → `pull --rebase` → 写文件 → `commit` → `push`。冲突自动中止并提示。本地仓库模式通过 `asyncio.subprocess` 执行 git 命令；远程仓库通过 GitHub API。

**面板可拖拽** — 文件树、编辑区、预览区之间可拖动分隔条调整宽度，编辑器与预览滚动同步。

**权限管理** — RBAC 三级角色（Admin / Editor / Viewer），权限可细化到目录层级。支持用户组。鉴权模式可选：`authenticated`（JWT 登录）或 `open`（跳过鉴权）。

**状态持久化** — 刷新页面后自动恢复上次打开的文件和编辑内容，展开/收起的目录状态持久化到 localStorage。

---

## 配置参考

所有配置通过 `server/config.py` 的 `Settings` 类管理，环境变量前缀 `REPOPRESS_`。

### 服务

```bash
REPOPRESS_HOST=0.0.0.0
REPOPRESS_PORT=8000
REPOPRESS_DEBUG=false
```

### 数据库

```bash
REPOPRESS_DATABASE_URL=sqlite://data/repopress.db
```

### 认证

```bash
REPOPRESS_AUTH_MODE=authenticated    # "authenticated" | "open"
REPOPRESS_JWT_SECRET=<your-secret>   # 生产环境务必修改
REPOPRESS_JWT_ALGORITHM=HS256
REPOPRESS_JWT_EXPIRE_MINUTES=1440    # Token 有效期（分钟），默认 24h
```

- `auth_mode = "authenticated"`：需 JWT 登录，按角色和目录权限控制
- `auth_mode = "open"`：跳过鉴权

### Git

```bash
REPOPRESS_GIT_CLONE_DIR=data/repos
REPOPRESS_ENCRYPTION_KEY=<your-key>  # AES-256-CBC，加密数据库中的 Access Token
```

### CLI

```bash
python -m server.cli start              # 启动
python -m server.cli stop               # 停止（PID 文件）
python -m server.cli restart            # 重启
python -m server.cli createsuperuser    # 交互式创建管理员
```

---

## 架构

### 数据流

```
Browser → Vue 3 SPA → REST API (FastAPI) → Git Repository (local / GitHub API)
                           ↓
                     SQLite (用户、权限、仓库配置 — 不存文档内容)
```

### 项目结构

```
repopress/
├── server/                  FastAPI 后端
│   ├── cli.py               start / stop / restart / createsuperuser
│   ├── main.py              FastAPI 入口 + 生命周期
│   ├── config.py            pydantic-settings 配置
│   ├── middleware.py        CORS / JWT / RateLimit / Logging
│   ├── models.py            Tortoise-ORM 模型（5 个）
│   ├── schemas.py           Pydantic v2 请求/响应
│   ├── services.py          业务逻辑（Auth / Admin / Doc / Tree）
│   ├── repo.py              GitProvider ABC + GitHub + Local 实现
│   └── routers/             auth / admin / docs 路由
├── web/                     Vue 3 前端
│   └── src/
│       ├── main.ts          入口
│       ├── router.ts        路由 + 守卫
│       ├── stores.ts        Pinia stores
│       ├── api.ts           ofetch HTTP 客户端
│       ├── composables.ts   useEditor / usePreview / useFileTree
│       ├── views/           Login / Editor / UserView / SettingView
│       └── components/      Header / Sidebar / FileTree / MarkdownEditor / PreviewPanel / BackToEditor
└── integrations/
    └── rspress/             Rspress EditLink 组件
```

### 技术栈

| 层 | 选型 |
|----|------|
| 前端 | Vue 3 + TypeScript + Vite + Pinia + Vue Router 4 |
| 编辑器 | CodeMirror 6 + markdown-it |
| UI | Naive UI + UnoCSS |
| HTTP 客户端 | ofetch |
| 后端 | FastAPI + Tortoise-ORM + Pydantic v2 |
| 数据库 | SQLite |
| Git 操作 | asyncio subprocess（本地）/ httpx（GitHub API） |
| 认证 | JWT + bcrypt |
| Token 加密 | AES-256-CBC |

---

## Git Provider

RepoPress 通过 `LocalGitProvider` 直接操作本地 Git 仓库（`asyncio.subprocess` 执行 git 命令）：

- 读取：`git show <ref>:<path>`
- 写入：`git checkout` → `git pull --rebase origin <branch>` → 写文件 → `git add + commit` → `git push`
- 冲突处理：rebase 失败自动 `git rebase --abort`，返回冲突提示
- 自动 stash 未提交的修改，rebase 后恢复

如需接入其他 Git 平台，实现 `GitProvider` 抽象基类的方法即可。详见 `server/repo.py`。

---

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
| GET | `/api/auth/user` | 当前用户信息 |

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

---

## License

[Apache 2.0](LICENSE)
