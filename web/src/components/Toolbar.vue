<script setup lang="ts">
const emit = defineEmits<{
  insert: [before: string, after: string]
  save: []
}>()

function action(before: string, after: string) {
  emit('insert', before, after)
}
</script>

<template>
  <div class="flex items-center gap-1 px-3 py-1.5 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
    <n-button secondary size="medium" title="Bold (Ctrl+B)" @click="action('**', '**')"><b>B</b></n-button>
    <n-button secondary size="medium" title="Italic (Ctrl+I)" @click="action('*', '*')"><i>I</i></n-button>
    <n-button secondary size="medium" title="Heading" @click="action('## ', '')">H</n-button>
    <n-button secondary size="medium" title="Link" @click="action('[', '](url)')">🔗</n-button>
    <n-button secondary size="medium" title="Image" @click="action('![', '](url)')">🖼</n-button>
    <n-button secondary size="medium" title="Inline Code" @click="action('`', '`')">&lt;/&gt;</n-button>
    <n-button secondary size="medium" title="Code Block" @click="action('```\n', '\n```')">```</n-button>
    <n-button secondary size="medium" title="Unordered List" @click="action('- ', '')">☰</n-button>
    <n-button secondary size="medium" title="Blockquote" @click="action('> ', '')">"</n-button>
  </div>
</template>
