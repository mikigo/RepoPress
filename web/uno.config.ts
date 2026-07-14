import { defineConfig, presetUno } from 'unocss'

export default defineConfig({
  presets: [presetUno()],
  shortcuts: {
    'app-layout': 'h-screen flex flex-col',
    'app-main': 'flex flex-1 overflow-hidden',
    'editor-panel': 'flex-1 flex flex-col min-w-0',
    'sidebar': 'w-64 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-y-auto',
    'preview-panel': 'flex-shrink-0 border-l border-gray-200 dark:border-gray-700',
  },
})
