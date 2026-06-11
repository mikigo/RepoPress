<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useRepoStore, useUIStore } from '../stores.js'
import { useEditor, usePreview } from '../composables.js'
import AppHeader from '../components/AppHeader.vue'
import AppSidebar from '../components/AppSidebar.vue'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import PreviewPanel from '../components/PreviewPanel.vue'

const route = useRoute()
const repo = useRepoStore()
const ui = useUIStore()
const { store: editorStore, fetchAndOpen, saveFile } = useEditor()
const preview = usePreview()

const editorComp = ref<InstanceType<typeof MarkdownEditor>>()
const previewComp = ref<InstanceType<typeof PreviewPanel>>()
let syncing = false
let scrollCleanup: (() => void) | null = null

function setupScrollSync() {
  scrollCleanup?.()
  const editorScroll = editorComp.value?.getScrollDOM()
  const previewScroll = previewComp.value?.getScrollContainer()
  if (!editorScroll || !previewScroll) return

  const onEditorScroll = () => {
    if (syncing) return
    syncing = true
    const max = editorScroll.scrollHeight - editorScroll.clientHeight
    const pct = max > 0 ? editorScroll.scrollTop / max : 0
    const pMax = previewScroll.scrollHeight - previewScroll.clientHeight
    previewScroll.scrollTop = pct * pMax
    syncing = false
  }

  const onPreviewScroll = () => {
    if (syncing) return
    syncing = true
    const max = previewScroll.scrollHeight - previewScroll.clientHeight
    const pct = max > 0 ? previewScroll.scrollTop / max : 0
    const eMax = editorScroll.scrollHeight - editorScroll.clientHeight
    editorScroll.scrollTop = pct * eMax
    syncing = false
  }

  editorScroll.addEventListener('scroll', onEditorScroll)
  previewScroll.addEventListener('scroll', onPreviewScroll)
  scrollCleanup = () => {
    editorScroll.removeEventListener('scroll', onEditorScroll)
    previewScroll.removeEventListener('scroll', onPreviewScroll)
  }
}

// Setup scroll sync when editor mounts or preview becomes visible
watch([() => editorStore.currentFile, () => ui.previewVisible], async () => {
  if (editorStore.currentFile && ui.previewVisible) {
    await nextTick()
    setupScrollSync()
  }
})

const EDITOR_CACHE_KEY = 'repopress_editor_state'

onMounted(async () => {
  await repo.fetchRepos()
  let repoId = route.params.repoId as string
  if (repoId && repo.repos.length > 0) {
    repo.setCurrentRepo(repoId)
    await repo.fetchTree()
  } else if (repo.repos.length > 0) {
    repo.setCurrentRepo(repo.repos[0].id)
    await repo.fetchTree()
  }

  // Restore last opened file from localStorage
  const filePath = route.params.path as string | undefined
  if (filePath && repo.currentRepoId) {
    await fetchAndOpen(filePath)
  } else {
    try {
      const saved = JSON.parse(localStorage.getItem(EDITOR_CACHE_KEY) || '{}')
      if (saved.currentFile && saved.content !== undefined) {
        editorStore.openFile(saved.currentFile, saved.content)
        preview.render(saved.content)
      }
    } catch { /* ignore */ }
  }
})

watch(() => editorStore.content, (val) => {
  if (val !== undefined) {
    preview.render(val)
  }
})

// Persist editor state
watch([() => editorStore.currentFile, () => editorStore.content], ([file, content]) => {
  if (file) {
    localStorage.setItem(EDITOR_CACHE_KEY, JSON.stringify({ currentFile: file, content }))
  } else {
    localStorage.removeItem(EDITOR_CACHE_KEY)
  }
})

// --- save flow ---
const showSaveDialog = ref(false)
const savePhase = ref<'confirm' | 'saving' | 'done'>('confirm')
const saveResult = ref<{ success: boolean; message: string } | null>(null)

function handleSave() {
  if (showSaveDialog.value) return  // Already open, ignore duplicate trigger
  savePhase.value = 'confirm'
  saveResult.value = null
  showSaveDialog.value = true
}

async function doSave() {
  savePhase.value = 'saving'
  try {
    const result = await saveFile()
    // Handle conflict
    if (result?.conflict) {
      saveResult.value = {
        success: false,
        message: '检测到远程仓库有新的提交，与本地修改存在冲突。请手动处理冲突后重试。',
      }
    } else if (result?.push) {
      const push = result.push
      saveResult.value = {
        success: push.success,
        message: push.success
          ? (push.detail || '推送成功')
          : (push.error || '推送失败'),
      }
    } else {
      saveResult.value = { success: true, message: '保存成功' }
    }
  } catch (e: any) {
    saveResult.value = { success: false, message: e?.data?.detail || e?.message || '保存失败' }
  }
  savePhase.value = 'done'
}

function closeSaveDialog() {
  showSaveDialog.value = false
  savePhase.value = 'confirm'
  saveResult.value = null
}

// --- resizable panels ---
const sidebarWidth = ref(256)
const previewRatio = ref(0.5)
let dragging: 'sidebar' | 'preview' | null = null

function startDrag(type: 'sidebar' | 'preview') {
  dragging = type
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onDrag(e: MouseEvent) {
  const appMain = document.querySelector('.app-main')
  if (!appMain) return
  const rect = appMain.getBoundingClientRect()
  if (dragging === 'sidebar') {
    sidebarWidth.value = Math.max(160, Math.min(480, e.clientX - rect.left))
  } else if (dragging === 'preview') {
    const rightEdge = rect.right - e.clientX
    previewRatio.value = Math.max(0.15, Math.min(0.75, rightEdge / rect.width))
  }
}

function stopDrag() {
  dragging = null
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

const editorPanelStyle = computed(() => {
  if (ui.previewVisible) {
    return { flex: `1 1 ${(1 - previewRatio.value) * 100}%` }
  }
  return { flex: '1 1 auto' }
})

const previewPanelStyle = computed(() => ({
  width: `${previewRatio.value * 100}%`,
}))
</script>

<template>
  <div class="app-layout">
    <AppHeader @save="handleSave" />

    <!-- Save confirmation dialog -->
    <n-modal :show="showSaveDialog" :mask-closable="false" :closable="false" preset="card" style="width:320px">
      <template #header><span class="text-15 font-semibold">保存文档</span></template>
      <!-- Phase: confirm -->
      <template v-if="savePhase === 'confirm'">
        <p class="text-13 leading-relaxed mb-4">确认是否保存，保存后将提交到文档仓库。</p>
        <div class="flex justify-end gap-2">
          <n-button size="tiny" @click="closeSaveDialog">取消</n-button>
          <n-button size="tiny" type="primary" @click="doSave">确定</n-button>
        </div>
      </template>

      <!-- Phase: saving -->
      <template v-else-if="savePhase === 'saving'">
        <div class="flex items-center justify-center gap-2 py-1">
          <n-spin size="small" />
          <span class="text-13 text-gray-500">正在保存并推送到仓库...</span>
        </div>
      </template>

      <!-- Phase: done -->
      <template v-else-if="savePhase === 'done'">
        <n-alert :type="saveResult?.success ? 'success' : 'error'" :title="saveResult?.success ? '操作完成' : '操作失败'" class="mb-4">
          <p class="text-13">{{ saveResult?.message }}</p>
        </n-alert>
        <div class="flex justify-end">
          <n-button size="tiny" type="primary" @click="closeSaveDialog">确定</n-button>
        </div>
      </template>
    </n-modal>

    <div class="app-main">
      <AppSidebar v-if="ui.sidebarOpen" :style="{ width: sidebarWidth + 'px' }" />
      <!-- sidebar splitter -->
      <div
        v-if="ui.sidebarOpen"
        class="w-1 cursor-col-resize bg-transparent hover:bg-blue-400 flex-shrink-0 transition-colors"
        @mousedown="startDrag('sidebar')"
      />
      <div class="editor-panel" :style="editorPanelStyle">
        <MarkdownEditor
          ref="editorComp"
          v-if="editorStore.currentFile"
          :content="editorStore.content"
          @update:content="editorStore.setContent"
          @save="handleSave"
        />
        <div v-else class="flex items-center justify-center h-full text-gray-400">
          <div class="text-center">
            <div class="text-4xl mb-4">📝</div>
            <div>Select a file from the sidebar to start editing</div>
          </div>
        </div>
      </div>
      <!-- preview splitter -->
      <div
        v-if="ui.previewVisible"
        class="w-1 cursor-col-resize bg-transparent hover:bg-blue-400 flex-shrink-0 transition-colors"
        @mousedown="startDrag('preview')"
      />
      <div v-if="ui.previewVisible" class="preview-panel" :style="previewPanelStyle">
        <PreviewPanel ref="previewComp" :html="preview.renderedHtml" />
      </div>
    </div>
  </div>
</template>
