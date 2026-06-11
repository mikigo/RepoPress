<script setup lang="ts">
import { ref, watch } from 'vue'
import { useEditor, useFileTree } from '../composables.js'
import type { TreeItem } from '../stores.js'

const props = defineProps<{
  items: TreeItem[]
  depth: number
  selectedPath: string | null
}>()

const emit = defineEmits<{
  select: [path: string, item: TreeItem]
}>()

const { store: editorStore, fetchAndOpen } = useEditor()
const { loadChildren } = useFileTree()

const CACHE_KEY = 'repopress_tree_expanded'

function loadExpanded(): Record<string, boolean> {
  try {
    return JSON.parse(localStorage.getItem(CACHE_KEY) || '{}')
  } catch {
    return {}
  }
}

function saveExpanded(state: Record<string, boolean>) {
  localStorage.setItem(CACHE_KEY, JSON.stringify(state))
}

const expanded = ref<Record<string, boolean>>(loadExpanded())

function handleClick(item: TreeItem) {
  emit('select', item.path, item)
  if (item.type === 'dir') {
    expanded.value[item.path] = !expanded.value[item.path]
    if (expanded.value[item.path] && !item.children) {
      loadChildren(item)
    }
  } else {
    fetchAndOpen(item.path)
  }
}

watch(expanded, (val) => saveExpanded(val), { deep: true })

function getArrow(item: TreeItem): string {
  if (item.type !== 'dir') return ''
  return expanded.value[item.path] ? '▾' : '▸'
}

function getIcon(item: TreeItem) {
  if (item.type === 'dir') {
    return expanded.value[item.path] ? '📂' : '📁'
  }
  const ext = item.name.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    md: '📝', mdx: '📝', json: '📋', yaml: '📋', yml: '📋', toml: '📋',
    js: '📄', ts: '📄', vue: '📄', css: '🎨',
    png: '🖼', jpg: '🖼', jpeg: '🖼', gif: '🖼', svg: '🖼', gitkeep: '⚙',
  }
  return icons[ext || ''] || '📄'
}
</script>

<template>
  <div>
    <div v-for="item in items" :key="item.path" class="select-none">
      <div
        class="flex items-center gap-1 py-0.5 px-1 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
        :class="{
          'bg-blue-100 dark:bg-blue-900/60': selectedPath === item.path,
          'bg-blue-50 dark:bg-blue-900 font-medium': editorStore.currentFile === item.path,
        }"
        :style="{ paddingLeft: `${depth * 16 + 4}px` }"
        @click="handleClick(item)"
      >
        <span class="text-2xs w-3 text-center text-gray-400">{{ getArrow(item) }}</span>
        <span class="text-xs w-4 text-center">{{ getIcon(item) }}</span>
        <span class="truncate">{{ item.name }}</span>
      </div>
      <FileTree
        v-if="item.type === 'dir' && expanded[item.path] && item.children"
        :items="item.children"
        :depth="depth + 1"
        :selected-path="selectedPath"
        @select="(p, i) => emit('select', p, i)"
      />
    </div>
  </div>
</template>
