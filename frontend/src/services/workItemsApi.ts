import type {
  WorkCompletionWrite,
  WorkEventAttachment,
  WorkHistory,
  WorkHistoryEntryWrite,
  WorkItemEvent,
  WorkItemRead,
  WorkItemWrite,
  WorkListFilters,
  WorkSubjectRead,
  WorkSubjectWrite,
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
    if (filters.subjectId) query.set('subject_id', filters.subjectId)
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
  complete(id: string, payload: WorkCompletionWrite | string | null = null) {
    let body: WorkCompletionWrite | { note: string | null }
    if (typeof payload === 'string') body = { note: payload }
    else if (payload === null) body = { note: null }
    else body = payload
    return request<WorkItemRead>(`/${encodeURIComponent(id)}/complete`, {
      method: 'POST', body: JSON.stringify(body)
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
  history(id: string) {
    return request<WorkHistory>(`/${encodeURIComponent(id)}/history`)
  },
  addHistory(id: string, payload: WorkHistoryEntryWrite) {
    return request<WorkItemEvent>(`/${encodeURIComponent(id)}/history`, {
      method: 'POST', body: JSON.stringify(payload)
    })
  },
  updateHistory(id: string, eventId: string, payload: WorkHistoryEntryWrite) {
    return request<WorkItemEvent>(`/${encodeURIComponent(id)}/history/${encodeURIComponent(eventId)}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  },
  removeHistory(id: string, eventId: string) {
    return request<void>(`/${encodeURIComponent(id)}/history/${encodeURIComponent(eventId)}`, { method: 'DELETE' })
  },
  async addAttachment(id: string, eventId: string, file: File) {
    const form = new FormData()
    form.append('file', file)
    const response = await fetch(`/api/v1/work-items/${encodeURIComponent(id)}/history/${encodeURIComponent(eventId)}/attachments`, {
      method: 'POST', headers: { Accept: 'application/json' }, body: form
    })
    if (!response.ok) throw new Error(await errorMessage(response))
    return response.json() as Promise<WorkEventAttachment>
  },
  attachmentUrl(id: string, eventId: string, attachmentId: string) {
    return `/api/v1/work-items/${encodeURIComponent(id)}/history/${encodeURIComponent(eventId)}/attachments/${encodeURIComponent(attachmentId)}`
  },
  removeAttachment(id: string, eventId: string, attachmentId: string) {
    return request<void>(`/${encodeURIComponent(id)}/history/${encodeURIComponent(eventId)}/attachments/${encodeURIComponent(attachmentId)}`, { method: 'DELETE' })
  },
  subjects() {
    return request<WorkSubjectRead[]>('/subjects')
  },
  createSubject(payload: WorkSubjectWrite) {
    return request<WorkSubjectRead>('/subjects', { method: 'POST', body: JSON.stringify(payload) })
  },
  updateSubject(id: string, payload: WorkSubjectWrite) {
    return request<WorkSubjectRead>(`/subjects/${encodeURIComponent(id)}`, { method: 'PUT', body: JSON.stringify(payload) })
  },
  removeSubject(id: string) {
    return request<void>(`/subjects/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },
  remove(id: string) {
    return request<void>(`/${encodeURIComponent(id)}`, { method: 'DELETE' })
  }
}
