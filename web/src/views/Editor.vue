<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
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
const editor = useEditor()
const preview = usePreview()

onMounted(async () => {
  await repo.fetchRepos()
  const repoId = route.params.repoId as string
  if (repoId && repo.repos.length > 0) {
    repo.setCurrentRepo(repoId)
    await repo.fetchTree()
  } else if (repo.repos.length > 0) {
    repo.setCurrentRepo(repo.repos[0].id)
    await repo.fetchTree()
  }

  const filePath = route.params.path as string | undefined
  if (filePath && repo.currentRepoId) {
    await editor.openFile(filePath as string)
  }
})

watch(() => editor.content, (val) => {
  if (val !== undefined) {
    preview.render(val)
  }
})

function handleSave() {
  editor.saveFile()
}
</script>

<template>
  <div class="app-layout">
    <AppHeader @save="handleSave" />
    <div class="app-main">
      <AppSidebar v-if="ui.sidebarOpen" />
      <div class="editor-panel" :class="{ 'flex-1': !ui.previewVisible }">
        <MarkdownEditor
          v-if="editor.currentFile"
          :content="editor.content"
          @update:content="editor.setContent"
          @save="handleSave"
        />
        <div v-else class="flex items-center justify-center h-full text-gray-400">
          <div class="text-center">
            <div class="text-4xl mb-4">📝</div>
            <div>Select a file from the sidebar to start editing</div>
          </div>
        </div>
      </div>
      <div v-if="ui.previewVisible" class="preview-panel">
        <PreviewPanel :html="preview.renderedHtml" />
      </div>
    </div>
  </div>
</template>
