<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  html: string
}>()

const container = ref<HTMLDivElement>()
const scrollContainer = ref<HTMLDivElement>()

defineExpose({ getScrollContainer: () => scrollContainer.value })

watch(() => props.html, async () => {
  if (!container.value) return
  // Re-render Mermaid diagrams
  await nextTick()
  const mermaidElements = container.value.querySelectorAll('.language-mermaid')
  if (mermaidElements.length > 0) {
    try {
      const mermaid = (await import('mermaid')).default
      mermaid.initialize({ startOnLoad: false, theme: 'default' })
      for (const el of mermaidElements) {
        const code = el.textContent || ''
        const id = `mermaid-${Math.random().toString(36).slice(2)}`
        try {
          const { svg } = await mermaid.render(id, code)
          el.innerHTML = svg
        } catch {
          el.innerHTML = `<span class="text-red-500">Mermaid render error</span>`
        }
      }
    } catch {
      // mermaid not available
    }
  }
})
</script>

<template>
  <div class="absolute inset-0 flex flex-col">
    <div class="h-11 flex items-center px-3 border-b border-gray-200 dark:border-gray-700 font-medium text-sm flex-shrink-0 bg-white dark:bg-gray-900">
      Preview
    </div>
    <div ref="scrollContainer" class="flex-1 overflow-y-auto no-scrollbar">
      <div ref="container" class="markdown-preview" v-html="html" />
    </div>
  </div>
</template>
