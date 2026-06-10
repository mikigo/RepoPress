<script setup lang="ts">
import { ref } from 'vue'
import { useMessage } from 'naive-ui'
import { useUIStore } from '../stores.js'

const message = useMessage()
const ui = useUIStore()

function handleClearCache() {
  message.success('Cache cleared')
}
</script>

<template>
  <div class="p-6">
    <h1 class="text-2xl font-bold mb-6">Settings</h1>

    <n-card title="Appearance" class="mb-4">
      <n-form-item label="Dark Mode">
        <n-switch v-model:value="ui.darkMode" />
      </n-form-item>
    </n-card>

    <n-card title="Actions" class="mb-4">
      <n-space>
        <n-button @click="handleClearCache">Clear Cache</n-button>
      </n-space>
    </n-card>

    <n-card title="About">
      <p class="text-sm text-gray-500">
        RepoPress v0.1.0 — The Missing CMS Layer for Git-Based Documentation.
      </p>
    </n-card>
  </div>
</template>
