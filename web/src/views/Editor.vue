<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useRepoStore, useUIStore } from '../stores.js'
import { useEditor, usePreview } from '../composables.js'
import AppHeader from '../components/AppHeader.vue'
import AppSidebar from '../components/AppSidebar.vue'
import MarkdownEditor from '../components/MarkdownEditor.vue'
import PreviewPanel from '../components/PreviewPanel.vue'

const route = useRoute()
const repo = useRepoStore()
const ui = useUIStore()
const message = useMessage()
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
    requestAnimationFrame(() => { syncing = false })
  }

  const onPreviewScroll = () => {
    if (syncing) return
    syncing = true
    const max = previewScroll.scrollHeight - previewScroll.clientHeight
    const pct = max > 0 ? previewScroll.scrollTop / max : 0
    const eMax = editorScroll.scrollHeight - editorScroll.clientHeight
    editorScroll.scrollTop = pct * eMax
    requestAnimationFrame(() => { syncing = false })
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

function handleLocalSave() {
  message.success('本地已保存')
}

function handlePush() {
  if (!editorStore.isDirty) return  // No changes, nothing to push
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
      if (push.success) editorStore.markSaved()
      saveResult.value = {
        success: push.success,
        message: push.success
          ? (push.detail || '推送成功')
          : (push.error || '推送失败'),
      }
    } else {
      editorStore.markSaved()
      saveResult.value = { success: true, message: '推送成功' }
    }
  } catch (e: any) {
    saveResult.value = { success: false, message: e?.data?.detail || e?.message || '保存失败' }
  }
  savePhase.value = 'done'
}

function closeSaveDialog() {
  if (savePhase.value === 'saving') return
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
    <AppHeader @save="handlePush" />

    <!-- Save confirmation dialog -->
    <n-modal
      :show="showSaveDialog"
      :mask-closable="savePhase !== 'saving'"
      preset="card"
      role="dialog"
      :style="{ width: '400px', borderRadius: '12px' }"
      @esc="closeSaveDialog"
      @mask-click="closeSaveDialog"
      :closable="false"
    >
      <!-- Phase: confirm -->
      <div v-if="savePhase === 'confirm'" class="flex flex-col items-center text-center py-2">
        <div class="w-10 h-10 rounded-full bg-blue-50 flex items-center justify-center mb-4">
          <svg class="w-5 h-5 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-1">推送文档</h3>
        <p class="text-sm text-gray-500 mb-6">确认推送后，修改将提交并推送到文档仓库。</p>
        <div class="flex gap-3 w-full">
          <n-button class="flex-1" @click="closeSaveDialog">取消</n-button>
          <n-button class="flex-1" type="primary" @click="doSave">确定推送</n-button>
        </div>
      </div>

      <!-- Phase: saving -->
      <div v-else-if="savePhase === 'saving'" class="flex flex-col items-center text-center py-4">
        <n-spin size="medium" />
        <p class="text-sm text-gray-500 mt-4">正在保存并推送到仓库...</p>
      </div>

      <!-- Phase: done -->
      <div v-else-if="savePhase === 'done'" class="flex flex-col items-center text-center py-2">
        <div v-if="saveResult?.success" class="w-10 h-10 rounded-full bg-green-50 flex items-center justify-center mb-4">
          <svg class="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div v-else class="w-10 h-10 rounded-full bg-red-50 flex items-center justify-center mb-4">
          <svg class="w-5 h-5 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-gray-900 mb-1">{{ saveResult?.success ? '操作完成' : '操作失败' }}</h3>
        <p class="text-sm text-gray-500 mb-6">{{ saveResult?.message }}</p>
        <n-button class="w-full" type="primary" @click="closeSaveDialog">确定</n-button>
      </div>
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
          @save="handleLocalSave"
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
