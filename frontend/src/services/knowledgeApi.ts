import type {
  DomainNote,
  KnowledgeTargetType,
  WikiPageRead,
  WikiPageWrite
} from '../types/knowledge'

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
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const knowledgeApi = {
  wikiPages(search?: string, includeArchived = false) {
    const query = new URLSearchParams()
    if (search?.trim()) query.set('search', search.trim())
    if (includeArchived) query.set('include_archived', 'true')
    const suffix = query.toString() ? `?${query}` : ''
    return request<WikiPageRead[]>(`/wiki/pages${suffix}`)
  },
  wikiPage(id: string, includeArchived = false) {
    const query = includeArchived ? '?include_archived=true' : ''
    return request<WikiPageRead>(`/wiki/pages/${encodeURIComponent(id)}${query}`)
  },
  createWikiPage(payload: WikiPageWrite) {
    return request<WikiPageRead>('/wiki/pages', {
      method: 'POST',
      body: JSON.stringify(payload)
    })
  },
  updateWikiPage(id: string, payload: WikiPageWrite) {
    return request<WikiPageRead>(`/wiki/pages/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    })
  },
  archiveWikiPage(id: string) {
    return request<void>(`/wiki/pages/${encodeURIComponent(id)}`, { method: 'DELETE' })
  },
  notes(targetType: KnowledgeTargetType, targetId: string) {
    const query = new URLSearchParams({ target_type: targetType, target_id: targetId })
    return request<DomainNote[]>(`/notes?${query}`)
  },
  createNote(targetType: KnowledgeTargetType, targetId: string, content: string) {
    return request<DomainNote>('/notes', {
      method: 'POST',
      body: JSON.stringify({ target_type: targetType, target_id: targetId, content })
    })
  },
  updateNote(id: string, content: string) {
    return request<DomainNote>(`/notes/${encodeURIComponent(id)}`, {
      method: 'PUT',
      body: JSON.stringify({ content })
    })
  },
  deleteNote(id: string) {
    return request<void>(`/notes/${encodeURIComponent(id)}`, { method: 'DELETE' })
  }
}
