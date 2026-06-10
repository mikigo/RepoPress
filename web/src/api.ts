import { createFetch } from 'ofetch'
import { useAuthStore } from './stores.js'

const baseURL = '/api'

const $fetch = createFetch({
  defaults: {
    baseURL,
    onRequest({ options }) {
      const auth = useAuthStore()
      if (auth.token) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        ;(options.headers as any).Authorization = `Bearer ${auth.token}`
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        const auth = useAuthStore()
        auth.logout()
        window.location.href = '/login'
      }
    },
  },
})

export interface LoginResponse {
  access_token: string
  token_type: string
  user: import('./stores.js').User
}

export interface DocSaveRequest {
  repo_id: string
  path: string
  content: string
  message?: string
}

export interface DocRenameRequest {
  repo_id: string
  old_path: string
  new_path: string
  message?: string
}

export interface RepoCreateRequest {
  name: string
  git_url: string
  docs_dir?: string
  ssg_type?: string
  default_branch?: string
  access_token: string
  review_mode?: boolean
}

export interface RepoUpdateRequest {
  name?: string
  git_url?: string
  docs_dir?: string
  ssg_type?: string
  default_branch?: string
  access_token?: string
  review_mode?: boolean
  is_active?: boolean
}

export interface UserCreateRequest {
  username: string
  email: string
  display_name: string
  password: string
  is_superuser?: boolean
}

export interface UserUpdateRequest {
  email?: string
  display_name?: string
  password?: string
  is_active?: boolean
  is_superuser?: boolean
}

export interface PermissionRequest {
  user_id?: string
  group_id?: string
  role_id: string
  path_pattern: string
}

export const api = {
  auth: {
    login: (username: string, password: string) =>
      $fetch<LoginResponse>('/auth/login', {
        method: 'POST',
        body: { username, password },
      }),
    logout: () =>
      $fetch<void>('/auth/logout', { method: 'POST' }),
    getCurrentUser: () =>
      $fetch<import('./stores.js').User>('/auth/user'),
  },

  docs: {
    getTree: (repoId: string, path = '') =>
      $fetch<import('./stores.js').TreeItem[]>('/docs/tree', {
        params: { repo_id: repoId, path },
      }),
    getFile: (repoId: string, path: string) =>
      $fetch<{ content: string; sha: string; path: string }>(`/docs/${path}`, {
        params: { repo_id: repoId },
      }),
    saveFile: (data: DocSaveRequest) =>
      $fetch<{ path: string; sha: string; commit_url: string }>('/docs/save', {
        method: 'POST',
        body: data,
      }),
    deleteFile: (repoId: string, path: string) =>
      $fetch<void>(`/docs/${path}`, {
        method: 'DELETE',
        params: { repo_id: repoId },
      }),
    renameFile: (data: DocRenameRequest) =>
      $fetch<{ path: string }>('/docs/rename', {
        method: 'POST',
        body: data,
      }),
    getHistory: (repoId: string, path: string) =>
      $fetch<any[]>(`/docs/${path}/history`, {
        params: { repo_id: repoId },
      }),
  },

  admin: {
    getRepos: () =>
      $fetch<import('./stores.js').RepoConfig[]>('/admin/repos'),
    createRepo: (data: RepoCreateRequest) =>
      $fetch<import('./stores.js').RepoConfig>('/admin/repos', {
        method: 'POST',
        body: data,
      }),
    updateRepo: (id: string, data: RepoUpdateRequest) =>
      $fetch<import('./stores.js').RepoConfig>(`/admin/repos/${id}`, {
        method: 'PUT',
        body: data,
      }),
    deleteRepo: (id: string) =>
      $fetch<void>(`/admin/repos/${id}`, { method: 'DELETE' }),
    getUsers: () =>
      $fetch<import('./stores.js').User[]>('/admin/users'),
    createUser: (data: UserCreateRequest) =>
      $fetch<import('./stores.js').User>('/admin/users', {
        method: 'POST',
        body: data,
      }),
    updateUser: (id: string, data: UserUpdateRequest) =>
      $fetch<import('./stores.js').User>(`/admin/users/${id}`, {
        method: 'PUT',
        body: data,
      }),
    updatePermissions: (data: PermissionRequest[]) =>
      $fetch<void>('/admin/permissions', {
        method: 'PUT',
        body: data,
      }),
  },
}
