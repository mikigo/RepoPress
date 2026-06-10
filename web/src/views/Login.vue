<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores.js'

const router = useRouter()
const auth = useAuthStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!username.value || !password.value) return
  loading.value = true
  error.value = ''
  try {
    await auth.login(username.value, password.value)
    router.push('/editor')
  } catch (e: any) {
    error.value = e?.data?.detail || e?.message || 'Login failed'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
    <n-card class="w-96" title="RepoPress Login">
      <n-form @submit.prevent="handleLogin">
        <n-form-item label="Username">
          <n-input
            v-model:value="username"
            placeholder="Enter username"
            :disabled="loading"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-form-item label="Password">
          <n-input
            v-model:value="password"
            type="password"
            placeholder="Enter password"
            :disabled="loading"
            @keyup.enter="handleLogin"
          />
        </n-form-item>
        <n-alert v-if="error" type="error" class="mb-4">
          {{ error }}
        </n-alert>
        <n-button
          type="primary"
          block
          :loading="loading"
          attr-type="submit"
          @click="handleLogin"
        >
          Sign In
        </n-button>
      </n-form>
    </n-card>
  </div>
</template>
