<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view'
import { EditorState } from '@codemirror/state'
import { markdown, markdownLanguage } from '@codemirror/lang-markdown'
import { languages } from '@codemirror/language-data'
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands'
import { searchKeymap } from '@codemirror/search'
import { autocompletion } from '@codemirror/autocomplete'
import Toolbar from './Toolbar.vue'

const props = defineProps<{
  content: string
}>()

const emit = defineEmits<{
  'update:content': [value: string]
  'save': []
}>()

const editorRef = ref<HTMLDivElement>()
let view: EditorView | null = null
let updating = false

onMounted(async () => {
  await nextTick()
  if (!editorRef.value) return

  const saveKeymap = keymap.of([{
    key: 'Mod-s',
    run: () => {
      emit('save')
      return true
    },
    preventDefault: true,
  }])

  const extensions = [
    lineNumbers(),
    highlightActiveLine(),
    history(),
    EditorView.lineWrapping,
    markdown({
      base: markdownLanguage,
      codeLanguages: languages,
    }),
    autocompletion(),
    keymap.of([...defaultKeymap, ...historyKeymap, ...searchKeymap]),
    saveKeymap,
    EditorView.updateListener.of((update) => {
      if (update.docChanged && !updating) {
        emit('update:content', update.state.doc.toString())
      }
    }),
  ]

  const state = EditorState.create({
    doc: props.content || '',
    extensions,
  })

  view = new EditorView({
    state,
    parent: editorRef.value,
  })

  // Refresh CodeMirror when container resizes (e.g., preview toggle)
  resizeObserver = new ResizeObserver(() => {
    view?.requestMeasure()
  })
  resizeObserver.observe(editorRef.value)
})

watch(() => props.content, (newVal) => {
  if (view && newVal !== view.state.doc.toString()) {
    updating = true
    view.dispatch({
      changes: {
        from: 0,
        to: view.state.doc.length,
        insert: newVal,
      },
    })
    updating = false
  }
})

let resizeObserver: ResizeObserver | null = null

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  view?.destroy()
})

function getScrollDOM() {
  return view?.scrollDOM ?? null
}

defineExpose({ getScrollDOM })

function insertFormat(before: string, after: string) {
  if (!view) return
  const selection = view.state.selection.main
  const selectedText = view.state.doc.sliceString(selection.from, selection.to)
  view.dispatch({
    changes: {
      from: selection.from,
      to: selection.to,
      insert: before + selectedText + after,
    },
    selection: { anchor: selection.from + before.length, head: selection.from + before.length + selectedText.length },
  })
  view.focus()
}
</script>

<template>
  <div class="flex flex-col h-full">
    <Toolbar @insert="insertFormat" @save="$emit('save')" />
    <div ref="editorRef" class="flex-1 overflow-hidden" />
  </div>
</template>
