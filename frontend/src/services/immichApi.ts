import type {
  ImmichAlbumList,
  ImmichAssetLink,
  ImmichAssetLinkList,
  ImmichImagePage,
  ImmichImageQuery
} from '../types/immich'

export class ImmichApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

function queryString(values: Record<string, string | number | boolean | undefined>): string {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value))
  })
  const serialized = params.toString()
  return serialized ? `?${serialized}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/immich${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    let message = `Immich-Anfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep the HTTP fallback for binary or invalid error bodies.
    }
    throw new ImmichApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const immichApi = {
  albums: () => request<ImmichAlbumList>('/albums'),
  browse: (query: ImmichImageQuery = {}) => request<ImmichImagePage>(
    `/assets${queryString(query)}`
  ),
  links: (assetId: string) => request<ImmichAssetLinkList>(
    `/links${queryString({ asset_id: assetId })}`
  ),
  createLink: (assetId: string, immichAssetId: string) => request<ImmichAssetLink>(
    '/links',
    {
      method: 'POST',
      body: JSON.stringify({ asset_id: assetId, immich_asset_id: immichAssetId })
    }
  ),
  removeLink: (linkId: string) => request<void>(`/links/${linkId}`, { method: 'DELETE' })
}
