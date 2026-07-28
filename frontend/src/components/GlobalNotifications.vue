<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'

import { useNotificationStore, type NotificationType } from '../stores/notifications'

const notifications = useNotificationStore()
const timers = new Map<number, ReturnType<typeof setTimeout>>()

const icons: Record<NotificationType, string> = {
  success: 'mdi-check-circle-outline',
  error: 'mdi-alert-circle-outline',
  warning: 'mdi-alert-outline',
  info: 'mdi-information-outline'
}

watch(() => notifications.queue.map((item) => `${item.id}:${item.timeout}`).join('|'), () => {
  const activeIds = new Set(notifications.queue.map((item) => item.id))
  for (const [id, timer] of timers) {
    if (!activeIds.has(id)) {
      clearTimeout(timer)
      timers.delete(id)
    }
  }
  for (const item of notifications.queue) {
    if (item.timeout <= 0 || timers.has(item.id)) continue
    timers.set(item.id, setTimeout(() => notifications.dismiss(item.id), item.timeout))
  }
}, { immediate: true })

onBeforeUnmount(() => {
  for (const timer of timers.values()) clearTimeout(timer)
  timers.clear()
})
</script>

<template>
  <Teleport to="body">
    <div class="global-notification-stack" role="region" aria-label="Anwendungsmeldungen">
      <v-alert
        v-for="item in notifications.queue"
        :key="item.id"
        :type="item.type"
        :icon="icons[item.type]"
        variant="elevated"
        closable
        class="global-notification-item"
        @click:close="notifications.dismiss(item.id)"
      >
        {{ item.message }}
      </v-alert>
    </div>
  </Teleport>
</template>

<style>
.global-notification-stack {
  position: fixed;
  z-index: 32000;
  top: max(12px, env(safe-area-inset-top));
  left: 50%;
  width: min(720px, calc(100vw - 24px));
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}
.global-notification-item {
  pointer-events: auto;
  box-shadow: 0 10px 32px rgba(0, 0, 0, .28);
}
@media (max-width: 600px) {
  .global-notification-stack {
    top: max(8px, env(safe-area-inset-top));
    width: calc(100vw - 16px);
  }
}
</style>
