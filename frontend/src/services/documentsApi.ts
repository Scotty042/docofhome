import type {
  DocumentListRead,
  DocumentMoveRequest,
  DocumentMutationRead
} from '../types/documents'

export class DocumentsApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

async function errorMessage(response: Response): Promise<string> {
  let message = `Dokumentenoperation fehlgeschlagen (HTTP ${response.status})`
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') message = body.detail
    if (Array.isArray(body.detail)) {
      message = body.detail.map((entry) => entry.msg).filter(Boolean).join(', ') || message
    }
  } catch {
    // Keep the HTTP fallback when the backend did not return JSON.
  }
  return message
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/documents${path}`, {
    ...init,
    headers: {
      Accept: 'application/json',
      ...init?.headers
    }
  })
  if (!response.ok) throw new DocumentsApiError(await errorMessage(response), response.status)
  return response.json() as Promise<T>
}

function query(params: Record<string, string | boolean | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  const serialized = search.toString()
  return serialized ? `?${serialized}` : ''
}

export const documentsApi = {
  list: (path = '') => request<DocumentListRead>(query({ path })),
  createFolder: (parentPath: string, name: string) => request<DocumentMutationRead>(
    '/folders',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ parent_path: parentPath, name })
    }
  ),
  upload: (path: string, file: File, overwrite = false) => request<DocumentMutationRead>(
    `/upload${query({ path, filename: file.name, overwrite: overwrite || undefined })}`,
    {
      method: 'POST',
      headers: { 'Content-Type': file.type || 'application/octet-stream' },
      body: file
    }
  ),
  move: (payload: DocumentMoveRequest) => request<DocumentMutationRead>('/move', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }),
  remove: async (path: string): Promise<void> => {
    const response = await fetch(`/api/v1/documents${query({ path })}`, {
      method: 'DELETE',
      headers: { Accept: 'application/json' }
    })
    if (!response.ok) throw new DocumentsApiError(await errorMessage(response), response.status)
  },
  downloadUrl: (path: string) => `/api/v1/documents/download${query({ path })}`,
  download: async (path: string): Promise<Blob> => {
    const response = await fetch(`/api/v1/documents/download${query({ path })}`, {
      headers: { Accept: 'application/octet-stream' }
    })
    if (!response.ok) throw new DocumentsApiError(await errorMessage(response), response.status)
    return response.blob()
  }
}
