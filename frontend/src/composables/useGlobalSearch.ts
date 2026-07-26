import { computed, ref, watch, type Ref } from 'vue'

import { searchApi } from '../services/searchApi'
import type { SearchResponse, SearchResult } from '../types/search'

export interface GlobalSearchOptions {
  debounceMs?: number
  request?: (query: string, signal: AbortSignal) => Promise<SearchResponse>
}

export function isGlobalSearchShortcut(event: Pick<KeyboardEvent, 'key' | 'ctrlKey' | 'metaKey' | 'altKey'>) {
  const key = event.key.toLowerCase()
  const primaryShortcut = key === 'k' && (event.ctrlKey || event.metaKey) && !event.altKey
  const slashShortcut = event.key === '/' && !event.ctrlKey && !event.metaKey && !event.altKey
  return primaryShortcut || slashShortcut
}

export function isEditableSearchTarget(target: EventTarget | null) {
  if (typeof HTMLElement === 'undefined' || !(target instanceof HTMLElement)) return false
  const tagName = target.tagName.toLowerCase()
  return tagName === 'input' || tagName === 'textarea' || tagName === 'select' || target.isContentEditable
}

export function useGlobalSearch(options: GlobalSearchOptions = {}) {
  const query = ref('')
  const loading = ref(false)
  const error = ref<string | null>(null)
  const response = ref<SearchResponse | null>(null)
  const activeIndex = ref(-1)
  const normalizedQuery = computed(() => query.value.trim())
  const minimumReached = computed(() => normalizedQuery.value.length >= 2)
  const flatResults = computed<SearchResult[]>(() => (
    response.value?.groups.flatMap((group) => group.results) ?? []
  ))

  const debounceMs = options.debounceMs ?? 250
  const request = options.request ?? ((value: string, signal: AbortSignal) => (
    searchApi.search(value, { signal })
  ))
  let timer: ReturnType<typeof setTimeout> | undefined
  let controller: AbortController | undefined
  let generation = 0

  function cancelPending() {
    if (timer !== undefined) clearTimeout(timer)
    timer = undefined
    controller?.abort()
    controller = undefined
  }

  function clearResultState() {
    response.value = null
    error.value = null
    loading.value = false
    activeIndex.value = -1
  }

  async function execute(value: string, requestGeneration: number) {
    const requestController = new AbortController()
    controller = requestController
    loading.value = true
    error.value = null
    try {
      const result = await request(value, requestController.signal)
      if (requestGeneration !== generation) return
      response.value = result
      activeIndex.value = result.total > 0 ? 0 : -1
    } catch (reason) {
      if (requestGeneration !== generation || (reason instanceof Error && reason.name === 'AbortError')) {
        return
      }
      response.value = null
      error.value = reason instanceof Error ? reason.message : 'Die Suche konnte nicht ausgeführt werden.'
      activeIndex.value = -1
    } finally {
      if (controller === requestController) controller = undefined
      if (requestGeneration === generation) loading.value = false
    }
  }

  function schedule() {
    generation += 1
    const requestGeneration = generation
    cancelPending()
    response.value = null
    error.value = null
    activeIndex.value = -1
    const value = normalizedQuery.value
    if (value.length < 2) {
      loading.value = false
      return
    }
    timer = setTimeout(() => {
      timer = undefined
      void execute(value, requestGeneration)
    }, debounceMs)
  }

  function moveActive(step: number) {
    const count = flatResults.value.length
    if (!count) {
      activeIndex.value = -1
      return
    }
    const current = activeIndex.value < 0 ? (step > 0 ? -1 : 0) : activeIndex.value
    activeIndex.value = (current + step + count) % count
  }

  function activate(index: number) {
    if (index >= 0 && index < flatResults.value.length) activeIndex.value = index
  }

  function reset() {
    generation += 1
    cancelPending()
    query.value = ''
    clearResultState()
  }

  function dispose() {
    generation += 1
    cancelPending()
  }

  watch(query, schedule)

  return {
    query,
    normalizedQuery,
    minimumReached,
    loading,
    error,
    response,
    activeIndex,
    flatResults,
    moveActive,
    activate,
    reset,
    dispose
  }
}
