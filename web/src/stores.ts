import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { darkTheme } from 'naive-ui'
import { api } from './api.js'

export interface User {
  id: string
  username: string
  email: string
  display_name: string
  is_superuser: boolean
  is_active: boolean
}

export interface RepoConfig {
  id: string
  name: string
  local_path: string
  docs_dir: string
  ssg_type: string
  default_branch: string
  hidden_extensions: string
  is_active: boolean
  created_at: string
}

export interface TreeItem {
  name: string
  path: string
  type: 'file' | 'dir'
  children?: TreeItem[]
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_superuser ?? false)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  async function login(username: string, password: string) {
    const data = await api.auth.login(username, password)
    setToken(data.access_token)
    user.value = data.user
  }

  async function fetchUser() {
    user.value = await api.auth.getCurrentUser()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, isAuthenticated, isAdmin, login, fetchUser, logout, setToken }
})

export const useEditorStore = defineStore('editor', () => {
  const currentFile = ref<string | null>(null)
  const content = ref('')
  const originalContent = ref('')
  const isDirty = computed(() => content.value !== originalContent.value)

  function openFile(path: string, fileContent: string) {
    currentFile.value = path
    content.value = fileContent
    originalContent.value = fileContent
  }

  function setContent(newContent: string) {
    content.value = newContent
  }

  function markSaved() {
    originalContent.value = content.value
  }

  function closeFile() {
    currentFile.value = null
    content.value = ''
    originalContent.value = ''
  }

  return { currentFile, content, originalContent, isDirty, openFile, setContent, markSaved, closeFile }
})

export const useRepoStore = defineStore('repo', () => {
  const repos = ref<RepoConfig[]>([])
  const currentRepoId = ref<string | null>(null)
  const tree = ref<TreeItem[]>([])
  const loading = ref(false)

  const currentRepo = computed(() =>
    repos.value.find(r => r.id === currentRepoId.value) ?? null
  )

  async function fetchRepos() {
    repos.value = await api.admin.getRepos()
  }

  function setCurrentRepo(id: string) {
    currentRepoId.value = id
  }

  async function fetchTree(path = '') {
    if (!currentRepoId.value) return
    loading.value = true
    try {
      tree.value = await api.docs.getTree(currentRepoId.value, path)
    } finally {
      loading.value = false
    }
  }

  return { repos, currentRepoId, tree, loading, currentRepo, fetchRepos, setCurrentRepo, fetchTree }
})

export const useUIStore = defineStore('ui', () => {
  const sidebarOpen = ref(true)
  const previewVisible = ref(true)
  const darkMode = ref(false)

  const naiveTheme = computed(() => darkMode.value ? darkTheme : undefined)

  function toggleSidebar() {
    sidebarOpen.value = !sidebarOpen.value
  }

  function togglePreview() {
    previewVisible.value = !previewVisible.value
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
  }

  return { sidebarOpen, previewVisible, darkMode, naiveTheme, toggleSidebar, togglePreview, toggleDarkMode }
})
