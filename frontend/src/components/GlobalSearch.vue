<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'

import { isEditableSearchTarget, isGlobalSearchShortcut, useGlobalSearch } from '../composables/useGlobalSearch'
import { isSafeLocalRoute } from '../services/searchApi'
import type { SearchResult } from '../types/search'
import GlobalSearchResults from './GlobalSearchResults.vue'

const router = useRouter()
const route = useRoute()
const { mdAndUp } = useDisplay()
const desktopOpen = ref(false)
const mobileOpen = ref(false)
type FocusableField = { focus?: () => void; $el?: HTMLElement }

const desktopInput = ref<FocusableField | null>(null)
const mobileInput = ref<FocusableField | null>(null)
const {
  query,
  loading,
  error,
  response,
  activeIndex,
  flatResults,
  moveActive,
  activate,
  reset,
  dispose
} = useGlobalSearch()

function focusInput() {
  void nextTick(() => {
    window.requestAnimationFrame(() => {
      window.requestAnimationFrame(() => {
        const target = mdAndUp.value ? desktopInput.value : mobileInput.value
        const input = target?.$el?.querySelector('input') as HTMLInputElement | null
        if (input) {
          input.focus({ preventScroll: true })
          return
        }
        target?.focus?.()
      })
    })
  })
}

function openSearch() {
  if (mdAndUp.value) desktopOpen.value = true
  else mobileOpen.value = true
  focusInput()
}

function closeSearch() {
  desktopOpen.value = false
  mobileOpen.value = false
}

async function selectResult(result: SearchResult) {
  if (!isSafeLocalRoute(result.route)) {
    return
  }
  closeSearch()
  reset()
  await router.push(result.route)
}

function handleInputKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowDown') {
    event.preventDefault()
    moveActive(1)
  } else if (event.key === 'ArrowUp') {
    event.preventDefault()
    moveActive(-1)
  } else if (event.key === 'Enter') {
    const result = flatResults.value[activeIndex.value]
    if (result) {
      event.preventDefault()
      void selectResult(result)
    }
  } else if (event.key === 'Escape') {
    event.preventDefault()
    closeSearch()
  }
}

function handleGlobalKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && (desktopOpen.value || mobileOpen.value)) {
    event.preventDefault()
    closeSearch()
    return
  }
  if (!isGlobalSearchShortcut(event)) return
  if (event.key === '/' && isEditableSearchTarget(event.target)) return
  event.preventDefault()
  openSearch()
}

watch(query, () => {
  if (query.value.trim().length >= 2) {
    if (mdAndUp.value) desktopOpen.value = true
  }
})

watch(desktopOpen, (open) => {
  if (open) focusInput()
})
watch(mobileOpen, (open) => {
  if (open) focusInput()
})

watch(() => route.fullPath, closeSearch)
watch(mdAndUp, () => {
  closeSearch()
})

onMounted(() => window.addEventListener('keydown', handleGlobalKeydown, { capture: true }))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', handleGlobalKeydown, { capture: true })
  dispose()
})
</script>

<template>
  <div class="global-search-shell">
    <v-menu
      v-if="mdAndUp"
      v-model="desktopOpen"
      :close-on-content-click="false"
      location="bottom end"
      offset="8"
      width="680"
      max-width="calc(100vw - 32px)"
    >
      <template #activator="{ props: menuProps }">
        <v-text-field
          ref="desktopInput"
          v-model="query"
          v-bind="menuProps"
          class="global-search-field"
          density="compact"
          variant="solo-filled"
          flat
          hide-details
          clearable
          maxlength="100"
          prepend-inner-icon="mdi-magnify"
          placeholder="Hausdokumentation durchsuchen"
          aria-label="Globale Suche"
          @keydown="handleInputKeydown"
        >
          <template #append-inner>
            <v-chip size="x-small" variant="outlined">Ctrl K · /</v-chip>
          </template>
        </v-text-field>
      </template>
      <v-card class="search-menu-card" rounded="lg">
        <GlobalSearchResults
          :query="query"
          :loading="loading"
          :error="error"
          :response="response"
          :active-index="activeIndex"
          @activate="activate"
          @select="selectResult"
        />
      </v-card>
    </v-menu>

    <v-btn
      v-else
      icon="mdi-magnify"
      variant="text"
      aria-label="Globale Suche öffnen"
      title="Globale Suche öffnen (Ctrl+K oder /)"
      @click="openSearch"
    />

    <v-dialog v-model="mobileOpen" fullscreen transition="dialog-bottom-transition">
      <v-card>
        <v-toolbar flat border>
          <v-btn icon="mdi-arrow-left" aria-label="Suche schließen" @click="closeSearch" />
          <v-text-field
            ref="mobileInput"
            v-model="query"
            class="mobile-search-field mr-3"
            density="comfortable"
            variant="solo-filled"
            flat
            hide-details
            clearable
            maxlength="100"
            prepend-inner-icon="mdi-magnify"
            placeholder="Suchen"
            aria-label="Globale Suche"
            @keydown="handleInputKeydown"
          />
        </v-toolbar>
        <GlobalSearchResults
          :query="query"
          :loading="loading"
          :error="error"
          :response="response"
          :active-index="activeIndex"
          @activate="activate"
          @select="selectResult"
        />
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.global-search-shell {
  flex: 0 1 420px;
  min-width: 0;
  margin-inline: 16px;
}

.global-search-field {
  width: min(420px, 34vw);
  min-width: 280px;
}

.search-menu-card {
  overflow: hidden;
}

.mobile-search-field {
  min-width: 0;
}

@media (max-width: 1100px) {
  .global-search-field {
    width: 300px;
    min-width: 240px;
  }
}

@media (max-width: 959px) {
  .global-search-shell {
    flex: 0 0 auto;
    margin-inline: 4px;
  }
}
</style>
