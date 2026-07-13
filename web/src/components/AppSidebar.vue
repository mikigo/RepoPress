<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRepoStore, useEditorStore, type TreeItem } from '../stores.js'
import { useFileTree } from '../composables.js'
import FileTree from './FileTree.vue'

const repo = useRepoStore()
const editor = useEditorStore()
const { createFile, deleteItem } = useFileTree()

const selectedPath = ref<string | null>(null)
const selectedItem = ref<TreeItem | null>(null)

// Sync selectedPath when currentFile changes externally (e.g. edit link navigation)
watch(() => editor.currentFile, (path) => {
  selectedPath.value = path
})

function onSelect(path: string, item: TreeItem) {
  selectedPath.value = path
  selectedItem.value = item
}

// ---- create ----
const showNewFile = ref(false)
const newFileName = ref('')
const creating = ref(false)

const createParentPath = computed(() => {
  if (!selectedItem.value) return 'docs'
  if (selectedItem.value.type === 'dir') return selectedItem.value.path
  // file: use parent directory
  const parts = selectedItem.value.path.split('/')
  parts.pop()
  return parts.join('/') || 'docs'
})

async function handleCreate() {
  const name = newFileName.value.trim()
  if (!name) return
  const fileName = name.endsWith('.md') ? name : `${name}.md`
  creating.value = true
  try {
    await createFile(createParentPath.value, fileName)
    showNewFile.value = false
    newFileName.value = ''
  } finally {
    creating.value = false
  }
}

// ---- delete ----
const showDeleteConfirm = ref(false)
const deleting = ref(false)

function confirmDelete() {
  showDeleteConfirm.value = true
}

function cancelDelete() {
  showDeleteConfirm.value = false
}

async function handleDelete() {
  if (!selectedItem.value || selectedItem.value.type !== 'file') return
  showDeleteConfirm.value = false
  deleting.value = true
  try {
    await deleteItem(selectedItem.value.path)
    selectedPath.value = null
    selectedItem.value = null
  } finally {
    deleting.value = false
  }
}

const canDelete = computed(() =>
  selectedItem.value?.type === 'file'
)
</script>

<template>
  <div class="sidebar flex flex-col">
    <div class="flex items-center justify-between px-3 py-2.5 border-b border-gray-100 dark:border-gray-800">
      <span class="text-xs font-semibold tracking-wide text-gray-400 uppercase">Files</span>
      <div class="flex items-center rounded-md border border-gray-200 dark:border-gray-700 overflow-hidden">
        <button
          class="w-8 h-7 flex items-center justify-center text-gray-500 hover:text-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors duration-150"
          title="New file"
          @click="showNewFile = true"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 5v14m-7-7h14" />
          </svg>
        </button>
        <div class="w-px h-4 bg-gray-200 dark:bg-gray-700" />
        <button
          class="w-8 h-7 flex items-center justify-center transition-colors duration-150"
          :class="canDelete ? 'text-gray-500 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20' : 'text-gray-300 dark:text-gray-600 cursor-not-allowed'"
          :disabled="!canDelete"
          title="Delete"
          @click="confirmDelete"
        >
          <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 12h14" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDeleteConfirm" class="px-3 py-2 border-b border-red-100 dark:border-red-900/30 bg-red-50 dark:bg-red-900/10">
      <p class="text-xs text-red-600 dark:text-red-400 mb-2">确定删除 {{ selectedItem?.name }}？</p>
      <div class="flex items-center gap-1">
        <n-button size="tiny" type="error" :loading="deleting" @click="handleDelete">删除</n-button>
        <n-button size="tiny" @click="cancelDelete">取消</n-button>
      </div>
    </div>

    <!-- New file input -->
    <div v-if="showNewFile" class="px-3 py-2 border-b border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800/50">
      <div class="text-xs text-gray-400 mb-1">{{ createParentPath }}/</div>
      <div class="flex items-center gap-1">
        <n-input
          v-model:value="newFileName"
          size="tiny"
          placeholder="filename.md"
          :disabled="creating"
          @keyup.enter="handleCreate"
          @keyup.escape="showNewFile = false"
        />
        <n-button size="tiny" type="primary" :loading="creating" @click="handleCreate">创建</n-button>
        <n-button size="tiny" @click="showNewFile = false">取消</n-button>
      </div>
    </div>

    <div class="flex-1 overflow-y-auto p-2">
      <div v-if="repo.loading" class="flex justify-center p-4">
        <n-spin size="small" />
      </div>
      <div v-else-if="repo.tree.length === 0" class="text-center text-gray-400 text-sm p-4">
        <div v-if="!repo.currentRepoId">Select a repository</div>
        <div v-else>No files found</div>
      </div>
      <FileTree
        v-else
        :items="repo.tree"
        :depth="0"
        :selected-path="selectedPath"
        @select="onSelect"
      />
    </div>
  </div>
</template>
