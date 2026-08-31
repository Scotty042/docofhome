import type { PaperlessDocument } from '../types/paperless'
import type { WorkPaperlessLink } from '../types/work'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) return body.detail.map((entry) => entry.msg).filter(Boolean).join(', ')
  } catch {
    // Keep the HTTP fallback.
  }
  return `Anfrage fehlgeschlagen (HTTP ${response.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/paperless${path}`, {
    ...init,
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const paperlessApi = {
  search(q = '', pageSize = 25) {
    const query = new URLSearchParams({ q, page_size: String(pageSize) })
    return request<PaperlessDocument[]>(`/documents?${query}`)
  },
  link(eventId: string, documentId: number) {
    return request<WorkPaperlessLink>(`/events/${encodeURIComponent(eventId)}/documents`, {
      method: 'POST',
      body: JSON.stringify({ document_id: documentId })
    })
  },
  unlink(eventId: string, linkId: string) {
    return request<void>(`/events/${encodeURIComponent(eventId)}/documents/${encodeURIComponent(linkId)}`, {
      method: 'DELETE'
    })
  }
}
