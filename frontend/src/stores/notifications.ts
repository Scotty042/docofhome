import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

export type NotificationType = 'success' | 'error' | 'warning' | 'info'

export interface AppNotification {
  id: number
  type: NotificationType
  message: string
  timeout: number
}

const DEFAULT_TIMEOUTS: Record<NotificationType, number> = {
  success: 4000,
  error: 9000,
  warning: 7000,
  info: 6000
}

let nextNotificationId = 1

export const useNotificationStore = defineStore('notifications', () => {
  const queue = ref<AppNotification[]>([])
  const current = computed(() => queue.value[0] ?? null)

  function push(type: NotificationType, message: string, timeout?: number) {
    const normalized = message.trim()
    if (!normalized) return
    const last = queue.value.at(-1)
    if (last?.type === type && last.message === normalized) return
    queue.value.push({
      id: nextNotificationId++,
      type,
      message: normalized,
      timeout: timeout ?? DEFAULT_TIMEOUTS[type]
    })
  }

  function dismiss(id: number) {
    queue.value = queue.value.filter((item) => item.id !== id)
  }

  function dismissCurrent() {
    const item = current.value
    if (item) dismiss(item.id)
  }

  function clear() {
    queue.value = []
  }

  return {
    queue,
    current,
    push,
    dismiss,
    dismissCurrent,
    clear,
    success: (message: string, timeout?: number) => push('success', message, timeout),
    error: (message: string, timeout?: number) => push('error', message, timeout),
    warning: (message: string, timeout?: number) => push('warning', message, timeout),
    info: (message: string, timeout?: number) => push('info', message, timeout)
  }
})
