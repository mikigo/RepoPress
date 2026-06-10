<script setup lang="ts">
import { useUIStore } from './stores.js'

const ui = useUIStore()
</script>

<template>
  <n-config-provider :theme="ui.naiveTheme">
    <n-message-provider>
      <n-notification-provider>
        <n-dialog-provider>
          <router-view />
        </n-dialog-provider>
      </n-notification-provider>
    </n-message-provider>
  </n-config-provider>
</template>
