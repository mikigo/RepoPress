<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NButton, NTag, useMessage, useDialog } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useRepoStore, type RepoConfig } from '../stores.js'
import { api } from '../api.js'
import BackToEditor from '../components/BackToEditor.vue'

const message = useMessage()
const dialog = useDialog()
const repoStore = useRepoStore()

// --- Repo CRUD ---
const showRepoModal = ref(false)
const editingRepo = ref<Partial<RepoConfig> | null>(null)
const repoForm = ref({
  name: '',
  local_path: '',
  docs_dir: 'docs',
  ssg_type: 'vitepress',
  default_branch: 'main',
})

const repoColumns: DataTableColumns<RepoConfig> = [
  { title: 'Name', key: 'name' },
  {
    title: 'Repo ID',
    key: 'id',
    width: 140,
    render(row) {
      return h('div', { class: 'flex items-center gap-1' }, [
        h('code', { class: 'text-xs bg-gray-100 px-1 py-0.5 rounded', title: row.id }, row.id.slice(0, 8) + '...'),
        h(NButton, { size: 'tiny', text: true, onClick: () => { navigator.clipboard.writeText(row.id); message.success('Repo ID copied') } }, { default: () => '📋' }),
      ])
    },
  },
  { title: 'Local Path', key: 'local_path', ellipsis: { tooltip: true }, width: 240 },
  { title: 'Docs Dir', key: 'docs_dir', width: 90 },
  {
    title: 'SSG',
    key: 'ssg_type',
    width: 80,
    render(row) { return h(NTag, { size: 'small' }, { default: () => row.ssg_type }) },
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 150,
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(NButton, { size: 'small', onClick: () => editRepo(row) }, { default: () => 'Edit' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => removeRepo(row) }, { default: () => 'Delete' }),
      ])
    },
  },
]

function openCreateRepo() {
  editingRepo.value = null
  repoForm.value = { name: '', local_path: '', docs_dir: 'docs', ssg_type: 'rspress', default_branch: 'main' }
  showRepoModal.value = true
}

function editRepo(row: RepoConfig) {
  editingRepo.value = row
  repoForm.value = {
    name: row.name,
    local_path: row.local_path || '',
    docs_dir: row.docs_dir,
    ssg_type: row.ssg_type,
    default_branch: row.default_branch,
  }
  showRepoModal.value = true
}

async function saveRepo() {
  try {
    if (editingRepo.value?.id) {
      await api.admin.updateRepo(editingRepo.value.id, {
        name: repoForm.value.name,
        local_path: repoForm.value.local_path,
        docs_dir: repoForm.value.docs_dir,
        ssg_type: repoForm.value.ssg_type,
        default_branch: repoForm.value.default_branch,
      })
      message.success('Repository updated')
    } else {
      await api.admin.createRepo({
        name: repoForm.value.name,
        local_path: repoForm.value.local_path,
        docs_dir: repoForm.value.docs_dir,
        ssg_type: repoForm.value.ssg_type,
        default_branch: repoForm.value.default_branch,
      })
      message.success('Repository added')
    }
    showRepoModal.value = false
    await repoStore.fetchRepos()
  } catch (e: any) {
    message.error(e?.data?.detail || 'Failed to save repository')
  }
}

function removeRepo(row: RepoConfig) {
  dialog.warning({
    title: 'Delete Repository',
    content: `Are you sure you want to delete "${row.name}"?`,
    positiveText: 'Delete',
    negativeText: 'Cancel',
    onPositiveClick: async () => {
      try {
        await api.admin.deleteRepo(row.id)
        message.success('Repository deleted')
        await repoStore.fetchRepos()
      } catch (e: any) {
        message.error(e?.data?.detail || 'Failed to delete')
      }
    },
  })
}

// --- Hidden Extensions ---
const selectedRepoId = ref<string | null>(null)
const hiddenExtensions = ref('')
const savingExtensions = ref(false)

onMounted(async () => {
  await repoStore.fetchRepos()
  if (repoStore.currentRepoId) {
    selectedRepoId.value = repoStore.currentRepoId
  } else if (repoStore.repos.length > 0) {
    selectedRepoId.value = repoStore.repos[0].id
  }
  if (selectedRepoId.value) {
    const r = repoStore.repos.find(r => r.id === selectedRepoId.value)
    hiddenExtensions.value = r?.hidden_extensions || ''
  }
})

function onRepoChange(repoId: string) {
  selectedRepoId.value = repoId
  const r = repoStore.repos.find(r => r.id === repoId)
  hiddenExtensions.value = r?.hidden_extensions || ''
}

async function saveExtensions() {
  if (!selectedRepoId.value) {
    message.warning('Please select a repository')
    return
  }
  savingExtensions.value = true
  try {
    await api.admin.updateRepo(selectedRepoId.value, { hidden_extensions: hiddenExtensions.value })
    message.success('Saved')
    await repoStore.fetchRepos()
  } catch (e: any) {
    message.error(e?.data?.detail || 'Failed to save')
  } finally {
    savingExtensions.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-4xl">
    <div class="flex items-center gap-4 mb-6">
      <BackToEditor />
      <h1 class="text-2xl font-bold">Settings</h1>
    </div>

    <!-- Repositories -->
    <n-card title="Repositories" class="mb-6">
      <template #header-extra>
        <n-button type="primary" size="small" @click="openCreateRepo">Add Repository</n-button>
      </template>
      <n-data-table :columns="repoColumns" :data="repoStore.repos" :loading="repoStore.loading" />
      <div v-if="repoStore.repos.length === 0" class="text-center text-gray-400 py-8">
        No repositories yet. Click "Add Repository" to get started.
      </div>
    </n-card>

    <!-- Repo modal -->
    <n-modal v-model:show="showRepoModal" preset="card" :title="editingRepo ? 'Edit Repository' : 'Add Repository'" class="w-140">
      <n-form>
        <n-form-item label="Name">
          <n-input v-model:value="repoForm.name" placeholder="My Docs" />
        </n-form-item>
        <n-form-item label="Local Path">
          <n-input v-model:value="repoForm.local_path" placeholder="/home/user/my-docs" />
        </n-form-item>
        <n-form-item label="Docs Directory">
          <n-input v-model:value="repoForm.docs_dir" placeholder="docs" />
        </n-form-item>
        <n-form-item label="SSG Type">
          <n-select v-model:value="repoForm.ssg_type" :options="[
            { label: 'VitePress', value: 'vitepress' },
            { label: 'Docusaurus', value: 'docusaurus' },
            { label: 'Rspress', value: 'rspress' },
            { label: 'MkDocs', value: 'mkdocs' },
          ]" />
        </n-form-item>
        <n-form-item label="Default Branch">
          <n-input v-model:value="repoForm.default_branch" placeholder="main" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showRepoModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveRepo">Save</n-button>
        </div>
      </template>
    </n-modal>

    <!-- Hidden File Formats -->
    <n-card title="Hidden File Formats">
      <p class="text-sm text-gray-500 mb-4">
        File extensions listed here will be hidden from the file tree for the selected repository.
      </p>
      <n-form-item label="Repository">
        <n-select
          :value="selectedRepoId"
          :options="repoStore.repos.map(r => ({ label: r.name, value: r.id }))"
          placeholder="Select a repository"
          @update:value="onRepoChange"
        />
      </n-form-item>
      <n-form-item label="Hidden Extensions">
        <n-input
          v-model:value="hiddenExtensions"
          placeholder="e.g. .pdf, .png, .jpg, .zip"
          :disabled="!selectedRepoId"
        />
      </n-form-item>
      <n-button type="primary" :loading="savingExtensions" :disabled="!selectedRepoId" @click="saveExtensions">
        Save
      </n-button>
    </n-card>
  </div>
</template>
