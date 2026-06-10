<script setup lang="ts">
import { ref } from 'vue'
import { useEditor, useFileTree } from '../composables.js'
import type { TreeItem } from '../stores.js'

const props = defineProps<{
  items: TreeItem[]
  depth: number
}>()

const editor = useEditor()
const ft = useFileTree()

const expanded = ref<Record<string, boolean>>({})

async function toggle(item: TreeItem) {
  if (item.type === 'dir') {
    expanded.value[item.path] = !expanded.value[item.path]
    if (expanded.value[item.path] && !item.children) {
      await ft.loadChildren(item)
    }
  } else {
    await editor.openFile(item.path)
  }
}

function getIcon(item: TreeItem) {
  if (item.type === 'dir') {
    return expanded.value[item.path] ? '📂' : '📁'
  }
  const ext = item.name.split('.').pop()?.toLowerCase()
  const icons: Record<string, string> = {
    md: '📝',
    mdx: '📝',
    json: '📋',
    yaml: '📋',
    yml: '📋',
    toml: '📋',
    js: '📄',
    ts: '📄',
    vue: '📄',
    css: '🎨',
    png: '🖼',
    jpg: '🖼',
    jpeg: '🖼',
    gif: '🖼',
    svg: '🖼',
    gitkeep: '⚙',
  }
  return icons[ext || ''] || '📄'
}
</script>

<template>
  <div>
    <div
      v-for="item in items"
      :key="item.path"
      class="select-none"
    >
      <div
        class="flex items-center gap-1 py-0.5 px-1 rounded cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
        :class="{ 'bg-blue-50 dark:bg-blue-900 font-medium': editor.currentFile === item.path }"
        :style="{ paddingLeft: `${depth * 16 + 4}px` }"
        @click="toggle(item)"
      >
        <span class="text-xs w-4 text-center">{{ getIcon(item) }}</span>
        <span class="truncate">{{ item.name }}</span>
      </div>
      <FileTree
        v-if="item.type === 'dir' && expanded[item.path] && item.children"
        :items="item.children"
        :depth="depth + 1"
      />
    </div>
  </div>
</template>
