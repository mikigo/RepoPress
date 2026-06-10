<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NButton, NTag, useMessage, useDialog } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { type User } from '../stores.js'
import { api } from '../api.js'

const message = useMessage()
const dialog = useDialog()

const users = ref<User[]>([])
const loading = ref(false)
const showModal = ref(false)
const editingUser = ref<User | null>(null)
const form = ref({
  username: '',
  email: '',
  display_name: '',
  password: '',
  is_superuser: false,
})

const columns: DataTableColumns<User> = [
  { title: 'Username', key: 'username' },
  { title: 'Email', key: 'email' },
  { title: 'Display Name', key: 'display_name' },
  {
    title: 'Role',
    key: 'is_superuser',
    width: 100,
    render(row) {
      return h(NTag, {
        type: row.is_superuser ? 'error' : 'info',
        size: 'small',
      }, { default: () => row.is_superuser ? 'Admin' : 'User' })
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
    width: 120,
    render(row) {
      return h('div', { class: 'flex gap-2' }, [
        h(NButton, { size: 'small', onClick: () => editUser(row) }, { default: () => 'Edit' }),
      ])
    },
  },
]

onMounted(fetchUsers)

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await api.admin.getUsers()
  } catch (e: any) {
    message.error(e?.data?.detail || 'Failed to load users')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingUser.value = null
  form.value = { username: '', email: '', display_name: '', password: '', is_superuser: false }
  showModal.value = true
}

function editUser(row: User) {
  editingUser.value = row
  form.value = {
    username: row.username,
    email: row.email,
    display_name: row.display_name,
    password: '',
    is_superuser: row.is_superuser,
  }
  showModal.value = true
}

async function saveUser() {
  try {
    if (editingUser.value) {
      await api.admin.updateUser(editingUser.value.id, {
        email: form.value.email,
        display_name: form.value.display_name,
        is_superuser: form.value.is_superuser,
        ...(form.value.password ? { password: form.value.password } : {}),
      })
      message.success('User updated')
    } else {
      await api.admin.createUser({
        username: form.value.username,
        email: form.value.email,
        display_name: form.value.display_name,
        password: form.value.password,
        is_superuser: form.value.is_superuser,
      })
      message.success('User created')
    }
    showModal.value = false
    await fetchUsers()
  } catch (e: any) {
    message.error(e?.data?.detail || 'Failed to save user')
  }
}
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">User Management</h1>
      <n-button type="primary" @click="openCreate">Add User</n-button>
    </div>

    <n-data-table :columns="columns" :data="users" :loading="loading" />

    <n-modal v-model:show="showModal" preset="card" :title="editingUser ? 'Edit User' : 'Add User'" class="w-120">
      <n-form>
        <n-form-item label="Username">
          <n-input v-model:value="form.username" :disabled="!!editingUser" placeholder="Username" />
        </n-form-item>
        <n-form-item label="Email">
          <n-input v-model:value="form.email" placeholder="Email" />
        </n-form-item>
        <n-form-item label="Display Name">
          <n-input v-model:value="form.display_name" placeholder="Display Name" />
        </n-form-item>
        <n-form-item label="Password">
          <n-input v-model:value="form.password" type="password" :placeholder="editingUser ? 'Leave blank to keep current' : 'Password'" />
        </n-form-item>
        <n-form-item label="Admin">
          <n-switch v-model:value="form.is_superuser" />
        </n-form-item>
      </n-form>
      <template #footer>
        <div class="flex justify-end gap-2">
          <n-button @click="showModal = false">Cancel</n-button>
          <n-button type="primary" @click="saveUser">Save</n-button>
        </div>
      </template>
    </n-modal>
  </div>
</template>
