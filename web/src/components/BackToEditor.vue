<script setup lang="ts">
import { useRouter } from 'vue-router'

defineProps<{
  loading?: boolean
}>()

const router = useRouter()

function goBack() {
  router.push('/editor')
}
</script>

<template>
  <n-button
    size="medium"
    :loading="loading"
    @click="goBack"
  >
    <template #icon>
      <svg
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="15 18 9 12 15 6" />
      </svg>
    </template>
    Back to Editor
  </n-button>
</template>
