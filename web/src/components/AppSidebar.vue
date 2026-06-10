<script setup lang="ts">
import { useRepoStore } from '../stores.js'
import FileTree from './FileTree.vue'

const repo = useRepoStore()
</script>

<template>
  <div class="sidebar flex flex-col">
    <div class="p-3 border-b border-gray-200 dark:border-gray-700 font-medium text-sm">
      Files
    </div>
    <div class="flex-1 overflow-y-auto p-2">
      <div v-if="repo.loading" class="flex justify-center p-4">
        <n-spin size="small" />
      </div>
      <div v-else-if="repo.tree.length === 0" class="text-center text-gray-400 text-sm p-4">
        <div v-if="!repo.currentRepoId">Select a repository</div>
        <div v-else>No files found</div>
      </div>
      <FileTree v-else :items="repo.tree" :depth="0" />
    </div>
  </div>
</template>
