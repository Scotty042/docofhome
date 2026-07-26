<script setup lang="ts">
import { computed } from 'vue'

import { useNotificationStore, type NotificationType } from '../stores/notifications'

const notifications = useNotificationStore()

const icon = computed(() => ({
  success: 'mdi-check-circle-outline',
  error: 'mdi-alert-circle-outline',
  warning: 'mdi-alert-outline',
  info: 'mdi-information-outline'
} satisfies Record<NotificationType, string>)[notifications.current?.type ?? 'info'])

function updateVisibility(visible: boolean) {
  if (!visible) notifications.dismissCurrent()
}
</script>

<template>
  <v-snackbar
    v-if="notifications.current"
    :key="notifications.current.id"
    :model-value="true"
    :timeout="notifications.current.timeout"
    :color="notifications.current.type"
    location="top center"
    variant="elevated"
    class="global-notification"
    @update:model-value="updateVisibility"
  >
    <div class="d-flex align-center ga-3">
      <v-icon :icon="icon" />
      <span>{{ notifications.current.message }}</span>
    </div>
    <template #actions>
      <v-btn
        icon="mdi-close"
        variant="text"
        aria-label="Meldung schließen"
        title="Meldung schließen"
        @click="notifications.dismissCurrent"
      />
    </template>
  </v-snackbar>
</template>

<style>
.global-notification {
  z-index: 10000 !important;
}

.global-notification .v-snackbar__wrapper {
  max-width: min(680px, calc(100vw - 24px));
}

@media (max-width: 600px) {
  .global-notification {
    margin-top: max(8px, env(safe-area-inset-top));
  }
}
</style>
