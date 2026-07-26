import type {
  HomeAssistantAssetBindings,
  HomeAssistantAssetBindingsWrite,
  HomeAssistantAssetLink,
  HomeAssistantAssetLinkList,
  HomeAssistantDeviceList,
  HomeAssistantDeviceQuery,
  HomeAssistantEntityList,
  HomeAssistantEntityQuery,
  HomeAssistantEntity,
  HomeAssistantEntityRole,
  HomeAssistantObjectType,
  HomeAssistantOverview,
  HomeAssistantSelection,
  HomeAssistantSelectionWrite
} from '../types/homeAssistant'

async function errorMessage(response: Response): Promise<string> {
  let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
  try {
    const body = await response.json() as { detail?: string }
    if (body.detail) message = body.detail
  } catch {
    // Keep the HTTP fallback.
  }
  return message
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/home-assistant${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function queryString(values: Record<string, string | number | boolean | undefined>): string {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') params.set(key, String(value))
  })
  const serialized = params.toString()
  return serialized ? `?${serialized}` : ''
}

function linkPath(objectType: HomeAssistantObjectType, externalId: string): string {
  return `/links/${objectType}/${encodeURIComponent(externalId)}`
}

async function allEntities(
  query: Omit<HomeAssistantEntityQuery, 'offset' | 'limit'> = {}
): Promise<HomeAssistantEntity[]> {
  const items: HomeAssistantEntity[] = []
  const limit = 1000
  while (true) {
    const result = await request<HomeAssistantEntityList>(
      `/entities${queryString({
        ...query,
        refresh: query.refresh && items.length === 0 ? true : undefined,
        offset: items.length,
        limit
      })}`
    )
    items.push(...result.items)
    if (items.length >= result.total || result.items.length === 0) return items
  }
}

export const homeAssistantApi = {
  overview: (refresh = false) => request<HomeAssistantOverview>(
    `/overview${queryString({ refresh })}`
  ),
  devices: (query: HomeAssistantDeviceQuery = {}) => request<HomeAssistantDeviceList>(
    `/devices${queryString(query)}`
  ),
  entities: (query: HomeAssistantEntityQuery = {}) => request<HomeAssistantEntityList>(
    `/entities${queryString(query)}`
  ),
  allEntities,
  selection: () => request<HomeAssistantSelection>('/selection'),
  updateSelection: (payload: HomeAssistantSelectionWrite) => request<HomeAssistantSelection>(
    '/selection',
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  links: (assetId?: string) => request<HomeAssistantAssetLinkList>(
    `/links${queryString({ asset_id: assetId })}`
  ),
  assetBindings: (assetId: string, refresh = false) => request<HomeAssistantAssetBindings>(
    `/assets/${encodeURIComponent(assetId)}${queryString({ refresh })}`
  ),
  upsertLink: (
    objectType: HomeAssistantObjectType,
    externalId: string,
    assetId: string,
    role: HomeAssistantEntityRole = 'additional'
  ) => request<HomeAssistantAssetLink>(linkPath(objectType, externalId), {
    method: 'PUT',
    body: JSON.stringify({ asset_id: assetId, role })
  }),
  replaceAssetBindings: (assetId: string, payload: HomeAssistantAssetBindingsWrite) => (
    request<HomeAssistantAssetBindings>(`/assets/${encodeURIComponent(assetId)}/bindings`, {
      method: 'PUT',
      body: JSON.stringify(payload)
    })
  ),
  removeLink: (objectType: HomeAssistantObjectType, externalId: string) => request<void>(
    linkPath(objectType, externalId),
    { method: 'DELETE' }
  )
}
