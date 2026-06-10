<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { api, type PermissionRequest } from '../api.js'
import type { User } from '../stores.js'

const message = useMessage()
const users = ref<User[]>([])
const roles = ref<{ id: string; name: string }[]>([])
const permissions = ref<{ user_id?: string; role_id: string; path_pattern: string }[]>([])
const loading = ref(false)

onMounted(async () => {
  loading.value = true
  try {
    users.value = await api.admin.getUsers()
    // Default roles
    roles.value = [
      { id: 'editor', name: 'Editor' },
      { id: 'viewer', name: 'Viewer' },
    ]
  } catch (e: any) {
    message.error('Failed to load data')
  } finally {
    loading.value = false
  }
})

const newPermission = ref<PermissionRequest>({
  user_id: undefined,
  role_id: '',
  path_pattern: '',
})

async function addPermission() {
  if (!newPermission.value.role_id || !newPermission.value.path_pattern) return
  permissions.value.push({ ...newPermission.value })
  newPermission.value = { user_id: undefined, role_id: '', path_pattern: '' }
}

function removePermission(index: number) {
  permissions.value.splice(index, 1)
}

async function savePermissions() {
  try {
    await api.admin.updatePermissions(
      permissions.value.map(p => ({
        user_id: p.user_id || undefined,
        role_id: p.role_id,
        path_pattern: p.path_pattern,
      }))
    )
    message.success('Permissions updated')
  } catch (e: any) {
    message.error('Failed to save permissions')
  }
}
</script>

<template>
  <div class="p-6">
    <div class="flex items-center justify-between mb-4">
      <h1 class="text-2xl font-bold">Permission Management</h1>
      <n-button type="primary" @click="savePermissions">Save</n-button>
    </div>

    <n-card title="Path Permissions" class="mb-4">
      <div class="flex gap-2 mb-4">
        <n-select
          v-model:value="newPermission.user_id"
          :options="users.map(u => ({ label: u.username, value: u.id }))"
          placeholder="User (optional)"
          clearable
          class="w-40"
        />
        <n-select
          v-model:value="newPermission.role_id"
          :options="roles.map(r => ({ label: r.name, value: r.id }))"
          placeholder="Role"
          class="w-32"
        />
        <n-input
          v-model:value="newPermission.path_pattern"
          placeholder="Glob path (e.g., docs/dev/**)"
          class="flex-1"
        />
        <n-button type="primary" @click="addPermission" :disabled="!newPermission.role_id || !newPermission.path_pattern">
          Add
        </n-button>
      </div>

      <div v-if="permissions.length === 0" class="text-center text-gray-400 py-8">
        No permissions configured. Add a permission rule above.
      </div>

      <div v-else class="space-y-2">
        <div
          v-for="(perm, i) in permissions"
          :key="i"
          class="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded"
        >
          <span class="font-mono text-sm">{{ perm.path_pattern }}</span>
          <n-tag size="small">{{ roles.find(r => r.id === perm.role_id)?.name || perm.role_id }}</n-tag>
          <span v-if="perm.user_id" class="text-sm text-gray-500">
            User: {{ users.find(u => u.id === perm.user_id)?.username || perm.user_id }}
          </span>
          <span v-else class="text-sm text-gray-400">All users</span>
          <n-button size="tiny" type="error" @click="removePermission(i)" class="ml-auto">Remove</n-button>
        </div>
      </div>
    </n-card>

    <n-card title="Permission Help">
      <p class="text-sm text-gray-500">
        Use glob patterns to restrict access to specific directories:
      </p>
      <ul class="text-sm text-gray-500 mt-2 space-y-1">
        <li><code>docs/**</code> — All documentation</li>
        <li><code>docs/dev/**</code> — Dev docs only</li>
        <li><code>docs/blog/*.md</code> — Blog posts only</li>
      </ul>
    </n-card>
  </div>
</template>
