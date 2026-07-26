import type { DocumentLink, DocumentTargetType } from '../types/documentLinks'

async function message(response: Response) {
  try {
    const body = await response.json() as { detail?: string }
    return body.detail || `Dokumentenverknüpfung fehlgeschlagen (HTTP ${response.status})`
  } catch {
    return `Dokumentenverknüpfung fehlgeschlagen (HTTP ${response.status})`
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/document-links${path}`, {
    ...init,
    headers: { Accept: 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await message(response))
  return response.json() as Promise<T>
}

export const documentLinksApi = {
  list(targetType: DocumentTargetType, targetId: string) {
    const query = new URLSearchParams({ target_type: targetType, target_id: targetId })
    return request<DocumentLink[]>(`?${query}`)
  },
  create(targetType: DocumentTargetType, targetId: string, documentPath: string) {
    return request<DocumentLink>('', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        target_type: targetType,
        target_id: targetId,
        document_path: documentPath
      })
    })
  },
  async remove(linkId: string) {
    const response = await fetch(`/api/v1/document-links/${encodeURIComponent(linkId)}`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' }
    })
    if (!response.ok) throw new Error(await message(response))
  }
}
