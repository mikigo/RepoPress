<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore, useRepoStore, useEditorStore, useUIStore } from '../stores.js'

const emit = defineEmits<{ save: [] }>()

const router = useRouter()
const auth = useAuthStore()
const repo = useRepoStore()
const editor = useEditorStore()
const ui = useUIStore()

const dropdownOptions = computed(() => {
  if (auth.isAdmin) {
    return [
      { label: 'User', key: '/user' },
      { label: 'Setting', key: '/setting' },
      { type: 'divider' as const },
      { label: 'Logout', key: 'logout' },
    ]
  }
  return [
    { label: 'Logout', key: 'logout' },
  ]
})

function goTo(path: string) {
  router.push(path)
}

async function handleRepoChange(id: string) {
  repo.setCurrentRepo(id)
  await repo.fetchTree()
  editor.closeFile()
}

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <n-layout-header bordered class="h-14 flex items-center justify-between px-4 flex-shrink-0">
    <div class="flex items-center gap-4">
      <n-button text @click="ui.toggleSidebar">
        <template #icon>
          <span class="text-lg">☰</span>
        </template>
      </n-button>
      <span class="text-lg font-bold cursor-pointer" @click="goTo('/editor')">RepoPress</span>

      <n-select
        v-if="repo.repos.length > 0"
        :value="repo.currentRepoId"
        :options="repo.repos.map(r => ({ label: r.name, value: r.id }))"
        class="w-48"
        size="small"
        @update:value="handleRepoChange"
      />

      <n-button
        v-if="editor.currentFile"
        :disabled="!editor.isDirty"
        :type="editor.isDirty ? 'warning' : 'primary'"
        size="small"
        @click="$emit('save')"
      >
        {{ editor.isDirty ? '● Push' : 'Pushed' }}
      </n-button>
    </div>

    <div class="flex items-center gap-2">
      <n-button text @click="ui.togglePreview">
        <template #icon>
          <span class="text-lg">{{ ui.previewVisible ? '👁' : '👁‍🗨' }}</span>
        </template>
      </n-button>

      <n-dropdown trigger="click" :options="dropdownOptions" @select="(k: string) => k === 'logout' ? handleLogout() : goTo(k)">
        <n-button text>
          <template #icon>
            <span class="text-lg">👤</span>
          </template>
          {{ auth.user?.username }}
        </n-button>
      </n-dropdown>
    </div>
  </n-layout-header>
</template>
