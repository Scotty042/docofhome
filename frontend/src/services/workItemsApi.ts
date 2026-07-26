import type {
  WorkItemEvent,
  WorkItemRead,
  WorkItemWrite,
  WorkListFilters,
  WorkSummary
} from '../types/work'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail.map((entry) => entry.msg).filter(Boolean).join(', ')
    }
  } catch {
    // Keep the HTTP fallback for non-JSON responses.
  }
  return `Anfrage fehlgeschlagen (HTTP ${response.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/work-items${path}`, {
    ...init,
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const workItemsApi = {
  list(filters: WorkListFilters = {}) {
    const query = new URLSearchParams()
    if (filters.status) query.set('status', filters.status)
    if (filters.itemType) query.set('item_type', filters.itemType)
    if (filters.targetType) query.set('target_type', filters.targetType)
    if (filters.targetId) query.set('target_id', filters.targetId)
    const suffix = query.toString() ? `?${query}` : ''
    return request<WorkItemRead[]>(suffix)
  },
  summary() {
    return request<WorkSummary>('/summary')
  },
  upcoming(days = 3) {
    return request<WorkItemRead[]>(`/upcoming?days=${days}`)
  },
  create(payload: WorkItemWrite) {
    return request<WorkItemRead>('', { method: 'POST', body: JSON.stringify(payload) })
  },
  update(id: string, payload: WorkItemWrite) {
    return request<WorkItemRead>(`/${encodeURIComponent(id)}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  },
  complete(id: string, note: string | null = null) {
    return request<WorkItemRead>(`/${encodeURIComponent(id)}/complete`, {
      method: 'POST', body: JSON.stringify({ note })
    })
  },
  cancel(id: string) {
    return request<WorkItemRead>(`/${encodeURIComponent(id)}/cancel`, { method: 'POST' })
  },
  reopen(id: string) {
    return request<WorkItemRead>(`/${encodeURIComponent(id)}/reopen`, { method: 'POST' })
  },
  events(id: string) {
    return request<WorkItemEvent[]>(`/${encodeURIComponent(id)}/events`)
  },
  remove(id: string) {
    return request<void>(`/${encodeURIComponent(id)}`, { method: 'DELETE' })
  }
}
