<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSettingsStore } from '../stores/settings'

const route = useRoute()
const router = useRouter()
const settings = useSettingsStore()
const retrying = ref(false)
const retryError = ref<string | null>(null)
const message = computed(() => retryError.value ?? settings.error ?? 'Setup-Status nicht verfügbar')

async function retry() {
  retrying.value = true
  retryError.value = null
  try {
    const completed = await settings.fetchSetupStatus(true)
    if (!completed) {
      await router.replace({ name: 'setup' })
      return
    }

    const requestedPath = typeof route.query.from === 'string' ? route.query.from : '/'
    const safePath = requestedPath.startsWith('/')
      && !requestedPath.startsWith('/setup')
      && !requestedPath.startsWith('/unavailable')
      ? requestedPath
      : '/'
    await router.replace(safePath)
  } catch (reason) {
    retryError.value = reason instanceof Error
      ? reason.message
      : 'Das Backend ist weiterhin nicht erreichbar.'
  } finally {
    retrying.value = false
  }
}
</script>

<template>
  <div class="unavailable-shell">
    <v-card class="unavailable-card" rounded="xl" elevation="12">
      <v-avatar color="warning" variant="tonal" size="80" class="mb-5">
        <v-icon icon="mdi-server-network-off" size="42" />
      </v-avatar>
      <h1>DocOfHome ist gerade nicht erreichbar</h1>
      <p class="text-medium-emphasis mt-3 mb-5">
        Der Einrichtungsstatus konnte nicht geladen werden. Deine vorhandene Konfiguration wurde
        nicht verändert und der First-Run-Wizard wird nicht erneut gestartet.
      </p>
      <v-alert type="warning" variant="tonal" class="mb-6 text-left">
        {{ message }}
      </v-alert>
      <v-btn
        color="primary"
        size="large"
        prepend-icon="mdi-refresh"
        :loading="retrying"
        @click="retry"
      >
        Erneut versuchen
      </v-btn>
    </v-card>
  </div>
</template>

<style scoped>
.unavailable-shell {
  display: grid;
  min-height: 100vh;
  padding: 1.5rem;
  place-items: center;
  background:
    radial-gradient(circle at 20% 20%, rgba(var(--v-theme-warning), 0.13), transparent 38%),
    rgb(var(--v-theme-background));
}

.unavailable-card {
  width: min(100%, 620px);
  padding: clamp(2rem, 7vw, 4rem);
  text-align: center;
}

.unavailable-card h1 {
  font-size: clamp(1.65rem, 5vw, 2.25rem);
  line-height: 1.2;
}
</style>
