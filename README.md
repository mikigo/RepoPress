# RepoPress

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](LICENSE)

> Git-based CMS for documentation sites. Edit Markdown/MDX in the browser, preview in real time, save and push — no Git CLI required.
>
> 基于 Git 的文档 CMS。在线编辑 Markdown/MDX，实时预览，保存即推送。零 Git 门槛。

RepoPress 是搭建在文档站点和 Git 仓库之间的一层 CMS。接入仓库后即可在浏览器中编辑文档、预览效果、保存后自动提交推送。不侵入 VitePress / Rspress / Docusaurus / MkDocs Material 的现有项目结构和构建流程。

**核心原则：Git 是唯一数据源。** RepoPress 不持有文档内容——文档始终在你的 Git 仓库中，服务端数据库仅存储用户、权限和仓库连接配置。

---

## 部署

### 环境要求

- Python 3.8+
- Node.js 18+
- Git

### 安装与启动

```bash
git clone <repo-url> repopress
cd repopress

# 构建前端
cd web
npm install
npm run build
mkdir -p ../server/static
cp -r dist/* ../server/static/

# 安装后端依赖
cd ../server
pip install -e .

# 启动
python -m cli start
```

服务启动后监听 `0.0.0.0:8000`。

### Nginx 反向代理

```nginx
server {
    listen 80;
    server_name repopress.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
    }
}
```

### 创建管理员

```bash
cd server
python -m cli createsuperuser
```

---

## 接入文档站点

以 Rspress 为例。VitePress / Docusaurus / MkDocs Material 同理，在对应配置中设置 editLink 即可。

### 1. 添加仓库

管理员登录 RepoPress，进入 **Setting** → **Repositories** → **Add Repository**：

| 字段 | 说明 |
|------|------|
| Name | 仓库显示名称 |
| Local Path | 文档项目在服务器上的绝对路径 |
| Docs 目录 | 文档内容所在子目录（如 `docs`） |
| SSG 类型 | `rspress` / `vitepress` / `docusaurus` / `mkdocs` |

保存后仓库列表显示 **Repo ID**，点击 📋 复制。

### 2. 安装 EditLink 组件

将 RepoPress 提供的 EditLink 组件集成到文档项目中。该组件确保所有编辑按钮在同一窗口打开，避免多开标签页。

```bash
# 在文档项目根目录下
mkdir -p theme/components/EditLink
cp <repopress>/integrations/rspress/EditLink.tsx theme/components/EditLink/index.tsx
```

编辑 `theme/index.tsx`：

```tsx
import './index.css';
import { Layout } from '@rspress/core/theme-original';
import { EditLink } from './components/EditLink';

export { Layout, EditLink };
export * from '@rspress/core/theme-original';
```

### 3. 配置 editLink

在文档项目的配置文件中设置 editLink，指向 RepoPress 服务地址：

**Rspress** — `rspress.config.ts`

```typescript
export default defineConfig({
    themeConfig: {
        editLink: {
            docRepoBaseUrl: 'https://repopress.example.com/editor/<repo-id>/docs',
        },
    },
});
```

**VitePress** — `.vitepress/config.ts`

```typescript
export default defineConfig({
    themeConfig: {
        editLink: {
            pattern: 'https://repopress.example.com/editor/<repo-id>/docs/:path',
        },
    },
});
```

**Docusaurus** — `docusaurus.config.js`

```javascript
module.exports = {
    presets: [['classic', {
        docs: { editUrl: 'https://repopress.example.com/editor/<repo-id>/docs/' },
    }]],
};
```

**MkDocs Material** — `mkdocs.yml`

```yaml
edit_uri: https://repopress.example.com/editor/<repo-id>/docs/
```

将 `<repo-id>` 替换为步骤 1 中复制的 Repo ID。

### 4. 验证

重新构建文档站点，打开任意文档页面，底部应出现"编辑此页面"链接。点击后跳转到 RepoPress 编辑器，编辑完成后 `Ctrl+S` 保存，自动提交推送至 Git 仓库。

---

## 核心功能

**在线编辑** — CodeMirror 6 驱动的 Markdown/MDX 编辑器。语法高亮、自动补全、格式化工具栏（加粗、斜体、标题、链接、图片、代码块、列表、引用），`Ctrl+S` 保存。

**文件管理** — 侧边栏文件树，支持展开收起、新建和删除文件/目录。可按文件后缀配置隐藏特定格式（如 `.pdf`、`.png`、`.zip`），管理员在 Setting 中统一配置，所有用户生效。

**实时预览** — 右侧分屏 Markdown 渲染，编辑内容即时刷新。支持标题、列表、代码块、表格、引用等元素。预览面板可切换显隐。

**保存流程** — 确认弹窗 → `pull --rebase` → 写入文件 → `commit` → `push`。冲突自动中止并提示，未提交的本地修改自动 stash 处理。

**权限管理** — RBAC 三级角色（Admin / Editor / Viewer），权限可细化到目录层级。支持用户组。鉴权模式可选：`authenticated`（JWT）或 `open`（免登录）。

**状态持久化** — 刷新页面后恢复上次打开的文件和编辑内容，目录展开状态持久化。

**面板可拖拽** — 文件树、编辑区和预览区之间可拖动分隔条调整宽度，编辑器与预览滚动同步。

**多仓库支持** — 同一 RepoPress 实例可管理多个文档仓库，各自独立配置，互不干扰。

---

## 配置参考

所有配置通过环境变量设置，前缀 `REPOPRESS_`。

### 服务

```bash
REPOPRESS_HOST=0.0.0.0
REPOPRESS_PORT=8000
```

### 数据库

```bash
REPOPRESS_DATABASE_URL=sqlite://data/repopress.db
```

### 认证

```bash
REPOPRESS_AUTH_MODE=authenticated      # "authenticated" | "open"
# JWT_SECRET 未设置时自动生成并持久化到 data/.jwt_secret
REPOPRESS_JWT_ALGORITHM=HS256
REPOPRESS_JWT_EXPIRE_MINUTES=1440      # Token 有效期（分钟），默认 24h
```

- `authenticated`：需 JWT 登录，按角色和目录权限控制
- `open`：跳过鉴权

### CLI

```bash
python -m cli start              # 启动服务
python -m cli stop               # 停止服务
python -m cli restart            # 重启服务
python -m cli createsuperuser    # 创建管理员
```

---

## 架构

### 数据流

```
Browser → Vue 3 SPA → REST API (FastAPI) → Local Git Repository
                           ↓
                     SQLite（用户、权限、仓库配置）
```

### 项目结构

```
repopress/
├── server/                  FastAPI 后端
│   ├── cli.py               服务管理（start / stop / restart / createsuperuser）
│   ├── main.py              应用入口与生命周期
│   ├── config.py            配置管理
│   ├── middleware.py         中间件（CORS / JWT / RateLimit）
│   ├── models.py            数据模型
│   ├── schemas.py           请求/响应模型
│   ├── services.py           业务逻辑
│   ├── repo.py               Git 操作层
│   └── routers/              路由模块（auth / admin / docs）
├── web/                     Vue 3 前端
│   └── src/
│       ├── views/            页面（Login / Editor / UserView / SettingView）
│       ├── components/       组件（Header / Sidebar / FileTree / MarkdownEditor / PreviewPanel）
│       ├── stores.ts         状态管理
│       ├── router.ts         路由配置
│       └── api.ts            HTTP 客户端
└── integrations/
    └── rspress/              Rspress 集成组件
```

### 技术栈

| 层 | 选型 |
|----|------|
| 前端框架 | Vue 3 + TypeScript + Vite |
| 状态管理 | Pinia |
| 路由 | Vue Router 4 |
| 编辑器 | CodeMirror 6 + markdown-it |
| UI 组件 | Naive UI + UnoCSS |
| 后端框架 | FastAPI |
| ORM | Tortoise-ORM |
| 数据校验 | Pydantic v2 |
| 数据库 | SQLite |
| Git 操作 | asyncio subprocess |
| 认证 | JWT + bcrypt |

---

## Git Provider

RepoPress 通过 `LocalGitProvider` 直接操作服务器上的本地 Git 仓库，底层使用 `asyncio.subprocess` 执行 git 命令：

- 读取：`git show <ref>:<path>`
- 保存：`git checkout` → `git pull --rebase origin <branch>` → 写入文件 → `git add` → `git commit` → `git push`
- 冲突处理：rebase 失败自动执行 `git rebase --abort` 并返回冲突提示
- 未提交修改：自动 `git stash` 暂存，rebase 后恢复

如需接入其他 Git 平台，实现 `GitProvider` 抽象基类的方法即可。详见 `server/repo.py`。

---

## API

### `/api/docs/`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/docs/{path}` | 获取文件内容 |
| POST | `/api/docs/save` | 创建或更新文件 |
| DELETE | `/api/docs/{path}` | 删除文件 |
| POST | `/api/docs/rename` | 重命名或移动文件 |
| GET | `/api/docs/{path}/history` | 文件提交历史 |
| GET | `/api/docs/tree` | 文件目录树 |

### `/api/auth/`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录 |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/user` | 获取当前用户信息 |

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
