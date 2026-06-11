<script setup lang="ts">
const emit = defineEmits<{
  insert: [before: string, after: string]
  save: []
}>()

function action(before: string, after: string) {
  emit('insert', before, after)
}

const groups = [
  {
    items: [
      { icon: 'bold', title: 'Bold', insert: ['**', '**'] as [string, string] },
      { icon: 'italic', title: 'Italic', insert: ['*', '*'] as [string, string] },
      { icon: 'code', title: 'Inline Code', insert: ['`', '`'] as [string, string] },
    ],
  },
  {
    items: [
      { icon: 'heading', title: 'Heading', insert: ['## ', ''] as [string, string] },
      { icon: 'list', title: 'Unordered List', insert: ['- ', ''] as [string, string] },
      { icon: 'quote', title: 'Blockquote', insert: ['> ', ''] as [string, string] },
    ],
  },
  {
    items: [
      { icon: 'link', title: 'Link', insert: ['[', '](url)'] as [string, string] },
      { icon: 'image', title: 'Image', insert: ['![', '](url)'] as [string, string] },
      { icon: 'codeblock', title: 'Code Block', insert: ['```\n', '\n```'] as [string, string] },
    ],
  },
]
</script>

<template>
  <div class="flex items-center h-11 px-2 gap-1 border-b border-gray-100 dark:border-gray-800 bg-white dark:bg-gray-900 flex-shrink-0">
    <template v-for="(group, gi) in groups" :key="gi">
      <div v-if="gi > 0" class="w-px h-5 mx-1 bg-gray-150 dark:bg-gray-800" />
      <template v-for="btn in group.items" :key="btn.title">
        <!-- Bold -->
        <button v-if="btn.icon === 'bold'"
          class="toolbar-btn font-bold" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 4h8a4 4 0 014 4 4 4 0 01-4 4H6z"/><path d="M6 12h9a4 4 0 014 4 4 4 0 01-4 4H6z"/></svg>
        </button>
        <!-- Italic -->
        <button v-else-if="btn.icon === 'italic'"
          class="toolbar-btn italic" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="4" x2="10" y2="4"/><line x1="14" y1="20" x2="5" y2="20"/><line x1="15" y1="4" x2="9" y2="20"/></svg>
        </button>
        <!-- Heading -->
        <button v-else-if="btn.icon === 'heading'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 12h12M6 20V4M18 20V4M8 20h8"/></svg>
        </button>
        <!-- Link -->
        <button v-else-if="btn.icon === 'link'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/></svg>
        </button>
        <!-- Image -->
        <button v-else-if="btn.icon === 'image'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
        </button>
        <!-- Code -->
        <button v-else-if="btn.icon === 'code'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg>
        </button>
        <!-- Code Block -->
        <button v-else-if="btn.icon === 'codeblock'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/><line x1="12" y1="4" x2="12" y2="20"/></svg>
        </button>
        <!-- List -->
        <button v-else-if="btn.icon === 'list'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
        </button>
        <!-- Quote -->
        <button v-else-if="btn.icon === 'quote'"
          class="toolbar-btn" :title="btn.title"
          @click="action(...btn.insert)">
          <svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg>
        </button>
      </template>
    </template>
  </div>
</template>

<style scoped>
.toolbar-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #6b7280;
  background: transparent;
  border: none;
  cursor: pointer;
  transition: color 150ms, background-color 150ms;
}
.toolbar-btn:hover {
  color: #374151;
  background: #f3f4f6;
}
.toolbar-btn:active {
  background: #e5e7eb;
}
.toolbar-btn:focus {
  outline: none;
  box-shadow: 0 0 0 2px rgba(96, 165, 250, 0.4);
  z-index: 1;
  position: relative;
}

/* dark mode */
.dark .toolbar-btn {
  color: #9ca3af;
}
.dark .toolbar-btn:hover {
  color: #e5e7eb;
  background: #1f2937;
}
.dark .toolbar-btn:active {
  background: #374151;
}
</style>
