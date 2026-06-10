<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NButton, NTag, useMessage, useDialog } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { useRepoStore, type RepoConfig } from '../stores.js'
import { api } from '../api.js'

const repo = useRepoStore()
const message = useMessage()
const dialog = useDialog()

const showModal = ref(false)
const editingRepo = ref<Partial<RepoConfig> | null>(null)
const form = ref({
  name: '',
  git_url: '',
  docs_dir: 'docs',
  ssg_type: 'vitepress',
  default_branch: 'main',
  access_token: '',
  review_mode: false,
})

const columns: DataTableColumns<RepoConfig> = [
  { title: 'Name', key: 'name' },
  { title: 'Git URL', key: 'git_url', ellipsis: { tooltip: true }, width: 280 },
  { title: 'Docs Dir', key: 'docs_dir', width: 100 },
  {
    title: 'SSG',
    key: 'ssg_type',
    width: 100,
    render(row) {
      return h(NTag, { size: 'small' }, { default: () => row.ssg_type })
    },
  },
  {
    title: 'Status',
    key: 'is_active',
    width: 80,
    render(row) {
      return h(NTag, {
        type: row.is_active ? 'success' : 'default',
        size: 'small',
      }, { default: () => row.is_active ? 'Active' : 'Inactive' })
    },
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 160,
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(NButton, { size: 'small', onClick: () => editRepo(row) }, { default: () => 'Edit' }),
        h(NButton, { size: 'small', type: 'error', onClick: () => removeRepo(row) }, { default: () => 'Delete' }),
      ])
    },
  },
]

onMounted(() => {
  repo.fetchRepos()
})

function openCreate() {
  editingRepo.value = null
  form.value = { name: '', git_url: '', docs_dir: 'docs', ssg_type: 'vitepress', default_branch: 'main', access_token: '', review_mode: false }
  showModal.value = true
}

function editRepo(row: RepoConfig) {
  editingRepo.value = row
  form.value = {
    name: row.name,
    git_url: row.git_url,
    docs_dir: row.docs_dir,
    ssg_type: row.ssg_type,
    default_branch: row.default_branch,
    access_token: '',
    review_mode: row.review_mode,
  }
  showModal.value = true
}

async function saveRepo() {
  try {
    if (editingRepo.value?.id) {
      await api.admin.updateRepo(editingRepo.value.id, {
        name: form.value.name,
        git_url: form.value.git_url,
        docs_dir: form.value.docs_dir,
        ssg_type: form.value.ssg_type,
        default_branch: form.value.default_branch,
        review_mode: form.value.review_mode,
        ...(form.value.access_token ? { access_token: form.value.access_token } : {}),
      })
      message.success('Repo updated')
    } else {
      await api.admin.createRepo({
        name: form.value.name,
        git_url: form.value.git_url,
        docs_dir: form.value.docs_dir,
        ssg_type: form.value.ssg_type,
        default_branch: form.value.default_branch,
        access_token: form.value.access_token,
        review_mode: form.value.review_mode,
      })
      message.success('Repo created')
    }
    showModal.value = false
    await repo.fetchRepos()
  } catch (e: any) {
    message.error(e?.data?.detail || 'Failed to save repo')
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
        message.success('Repo deleted')
        await repo.fetchRepos()
      } catch (e: any) {
        message.error(e?.data?.detail || 'Failed to delete repo')
      }
    },
  })
}
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">Repository Management</h1>
      <n-button type="primary" @click="openCreate">Add Repository</n-button>
    </div>

    <n-data-table :columns="columns" :data="repo.repos" :loading="repo.loading" />

    <n-modal v-model:show="showModal" preset="card" :title="editingRepo ? 'Edit Repository' : 'Add Repository'" class="w-160">
      <n-form>
        <n-form-item label="Name">
          <n-input v-model:value="form.name" placeholder="My Docs" />
        </n-form-item>
        <n-form-item label="Git URL">
          <n-input v-model:value="form.git_url" placeholder="https://github.com/owner/repo.git" />
        </n-form-item>
        <n-form-item label="Docs Directory">
          <n-input v-model:value="form.docs_dir" placeholder="docs" />
        </n-form-item>
        <n-form-item label="SSG Type">
          <n-select v-model:value="form.ssg_type" :options="[
            { label: 'VitePress', value: 'vitepress' },
            { label: 'Docusaurus', value: 'docusaurus' },
            { label: 'Rspress', value: 'rspress' },
            { label: 'MkDocs', value: 'mkdocs' },
          ]" />
        </n-form-item>
        <n-form-item label="Default Branch">
          <n-input v-model:value="form.default_branch" placeholder="main" />
        </n-form-item>
        <n-form-item label="Access Token">
          <n-input v-model:value="form.access_token" type="password" :placeholder="editingRepo ? 'Leave blank to keep current' : 'GitHub personal access token'" />
        </n-form-item>
        <n-form-item label="Review Mode">
          <n-switch v-model:value="form.review_mode" />
          <span class="ml-2 text-sm text-gray-500">Create PR instead of direct push</span>
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveRepo">Save</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>
