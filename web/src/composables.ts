import { reactive, ref, watch, onBeforeUnmount, type Ref } from 'vue'
import MarkdownIt from 'markdown-it'
import { useAuthStore, useRepoStore, useEditorStore, type TreeItem } from './stores.js'
import { api } from './api.js'
import router from './router.js'

export function useAuth() {
  const auth = useAuthStore()
  return auth
}

export function useEditor() {
  const store = useEditorStore()

  async function fetchAndOpen(path: string) {
    const repo = useRepoStore()
    if (!repo.currentRepoId) return
    const data = await api.docs.getFile(repo.currentRepoId, path)
    store.openFile(path, data.content)
  }

  async function saveFile(message?: string) {
    const repo = useRepoStore()
    if (!repo.currentRepoId || !store.currentFile) return
    const commitMsg = message || `docs: update ${store.currentFile}`
    const data = await api.docs.saveFile({
      repo_id: repo.currentRepoId,
      path: store.currentFile,
      content: store.content,
      message: commitMsg,
    })
    store.markSaved()
    return data as {
      commit_sha?: string
      mode: string
      conflict?: boolean
      rebase?: { success: boolean; error?: string }
      push?: { success: boolean; detail?: string; error?: string }
    }
  }

  return { store, fetchAndOpen, saveFile }
}

export function usePreview() {
  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
  })

  const renderedHtml = ref('')

  function render(content: string) {
    try {
      renderedHtml.value = md.render(content)
    } catch {
      renderedHtml.value = '<p style="color:red">Render error</p>'
    }
  }

  return reactive({ renderedHtml, render })
}

export function useFileTree() {
  const store = useRepoStore()

  async function loadChildren(item: TreeItem): Promise<TreeItem[] | undefined> {
    if (item.children && item.children.length > 0) return item.children
    const items = await api.docs.getTree(store.currentRepoId!, item.path)
    item.children = items
    return items
  }

  async function createFile(parentPath: string, name: string) {
    if (!store.currentRepoId) return
    const path = `${parentPath}/${name}`
    await api.docs.saveFile({
      repo_id: store.currentRepoId,
      path,
      content: '',
      message: `docs: create ${path}`,
    })
    await store.fetchTree()
  }

  async function deleteItem(path: string) {
    if (!store.currentRepoId) return
    await api.docs.deleteFile(store.currentRepoId, path)
    await store.fetchTree()
  }

  return { store, loadChildren, createFile, deleteItem }
}
