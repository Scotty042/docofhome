import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import { useNotificationStore } from './notifications'

describe('global notification queue', () => {
  beforeEach(() => setActivePinia(createPinia()))

  it('shows queued messages in FIFO order and allows manual dismissal', () => {
    const store = useNotificationStore()

    store.error('Speichern fehlgeschlagen')
    store.success('Gespeichert')

    expect(store.current?.message).toBe('Speichern fehlgeschlagen')
    expect(store.queue).toHaveLength(2)
    store.dismissCurrent()
    expect(store.current?.message).toBe('Gespeichert')
  })

  it('does not queue the same message twice in a row', () => {
    const store = useNotificationStore()

    store.error('Speichern fehlgeschlagen')
    store.error('Speichern fehlgeschlagen')

    expect(store.queue).toHaveLength(1)
  })

  it('keeps errors visible longer than success messages', () => {
    const store = useNotificationStore()

    store.error('Fehler')
    const errorTimeout = store.current?.timeout ?? 0
    store.clear()
    store.success('Erfolg')

    expect(errorTimeout).toBeGreaterThan(store.current?.timeout ?? 0)
  })
})
