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
  const editor = useEditorStore()

  async function openFile(path: string) {
    const repo = useRepoStore()
    if (!repo.currentRepoId) return
    const data = await api.docs.getFile(repo.currentRepoId, path)
    editor.openFile(path, data.content)
  }

  async function saveFile(message?: string) {
    const repo = useRepoStore()
    if (!repo.currentRepoId || !editor.currentFile) return
    const commitMsg = message || `docs: update ${editor.currentFile}`
    const data = await api.docs.saveFile({
      repo_id: repo.currentRepoId,
      path: editor.currentFile,
      content: editor.content,
      message: commitMsg,
    })
    editor.markSaved()
    return data
  }

  return { ...editor, openFile, saveFile }
}

export function usePreview() {
  const md = new MarkdownIt({
    html: true,
    linkify: true,
    typographer: true,
  })

  const state = reactive({
    renderedHtml: '',
  })

  function render(content: string) {
    try {
      state.renderedHtml = md.render(content)
    } catch {
      state.renderedHtml = '<p style="color:red">Render error</p>'
    }
  }

  return { ...state, render }
}

export function useFileTree() {
  const repo = useRepoStore()

  async function refresh() {
    await repo.fetchTree()
  }

  async function loadChildren(item: TreeItem): Promise<TreeItem[] | undefined> {
    if (item.children) return item.children
    const items = await api.docs.getTree(repo.currentRepoId!, item.path)
    item.children = items
    return items
  }

  async function createFile(parentPath: string, name: string) {
    if (!repo.currentRepoId) return
    const path = parentPath ? `${parentPath}/${name}` : name
    await api.docs.saveFile({
      repo_id: repo.currentRepoId,
      path,
      content: '',
      message: `docs: create ${path}`,
    })
    await repo.fetchTree()
  }

  async function createFolder(parentPath: string, name: string) {
    if (!repo.currentRepoId) return
    const path = parentPath ? `${parentPath}/${name}` : name
    // Create a .gitkeep to simulate folder creation
    await api.docs.saveFile({
      repo_id: repo.currentRepoId,
      path: `${path}/.gitkeep`,
      content: '',
      message: `docs: create folder ${path}`,
    })
    await repo.fetchTree()
  }

  async function deleteItem(path: string) {
    if (!repo.currentRepoId) return
    await api.docs.deleteFile(repo.currentRepoId, path)
    await repo.fetchTree()
  }

  async function renameItem(oldPath: string, newPath: string) {
    if (!repo.currentRepoId) return
    await api.docs.renameFile({
      repo_id: repo.currentRepoId,
      old_path: oldPath,
      new_path: newPath,
      message: `docs: rename ${oldPath} to ${newPath}`,
    })
    await repo.fetchTree()
  }

  return {
    tree: repo.tree,
    loading: repo.loading,
    refresh,
    loadChildren,
    createFile,
    createFolder,
    deleteItem,
    renameItem,
  }
}
