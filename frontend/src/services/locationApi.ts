import type { Page } from '../types/assets'
import type {
  Location,
  LocationListQuery,
  LocationTreeNode,
  LocationWrite
} from '../types/locations'

export class LocationApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

function queryString(values: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value))
  })
  const serialized = query.toString()
  return serialized ? `?${serialized}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
      if (typeof body.detail === 'string') message = body.detail
      if (Array.isArray(body.detail)) {
        message = body.detail.map((entry) => entry.msg).filter(Boolean).join(', ') || message
      }
    } catch {
      // Keep the HTTP fallback for non-JSON responses.
    }
    throw new LocationApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const locationApi = {
  list: (query: LocationListQuery = {}) => request<Page<Location>>(
    `/locations${queryString(query as Record<string, string | number | boolean | undefined>)}`
  ),
  tree: (includeDeleted = false) => request<LocationTreeNode[]>(
    `/locations/tree${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  get: (id: string, includeDeleted = false) => request<Location>(
    `/locations/${id}${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  create: (location: LocationWrite) => request<Location>('/locations', {
    method: 'POST', body: JSON.stringify(location)
  }),
  update: (id: string, location: LocationWrite) => request<Location>(`/locations/${id}`, {
    method: 'PUT', body: JSON.stringify(location)
  }),
  move: (id: string, parentId: string) => request<Location>(`/locations/${id}/move`, {
    method: 'POST', body: JSON.stringify({ parent_id: parentId })
  }),
  remove: (id: string) => request<void>(`/locations/${id}`, { method: 'DELETE' })
}
