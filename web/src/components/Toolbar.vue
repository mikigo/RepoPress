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
  <div class="flex items-center gap-0.5 px-2 py-1 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 flex-shrink-0">
    <n-button text size="small" title="Bold (Ctrl+B)" @click="action('**', '**')"><b>B</b></n-button>
    <n-button text size="small" title="Italic (Ctrl+I)" @click="action('*', '*')"><i>I</i></n-button>
    <n-button text size="small" title="Heading" @click="action('## ', '')">H</n-button>
    <n-button text size="small" title="Link" @click="action('[', '](url)')">🔗</n-button>
    <n-button text size="small" title="Image" @click="action('![', '](url)')">🖼</n-button>
    <n-button text size="small" title="Code" @click="action('`', '`')">&lt;/&gt;</n-button>
    <n-button text size="small" title="Code Block" @click="action('```\n', '\n```')">```</n-button>
    <n-button text size="small" title="List" @click="action('- ', '')">☰</n-button>
    <n-button text size="small" title="Blockquote" @click="action('> ', '')">"</n-button>
    <div class="flex-1" />
    <n-button size="tiny" type="primary" @click="$emit('save')">Save</n-button>
  </div>
</template>
