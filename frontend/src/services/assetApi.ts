import type {
  Asset,
  AssetDuplicateWrite,
  AssetListQuery,
  AssetReplacement,
  AssetSeriesRead,
  AssetSeriesWrite,
  AssetType,
  AssetTypeWrite,
  AssetWrite,
  Label,
  LabelWrite,
  Location,
  Page,
  Product,
  ProductImageSearch,
  ProductImageUpload,
  ProductWrite,
  Relationship
} from '../types/assets'

export class AssetApiError extends Error {
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
    throw new AssetApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

async function uploadRequest<T>(path: string, data: FormData, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`/api/v1${path}`, { method: 'POST', body: data, signal })
  if (!response.ok) {
    let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch {
      // Keep fallback.
    }
    throw new AssetApiError(message, response.status)
  }
  return response.json() as Promise<T>
}

async function requestAll<T>(path: string, includeDeleted = false): Promise<T[]> {
  const items: T[] = []
  let page = 1
  let pages = 1
  do {
    const result = await request<Page<T>>(
      `${path}${queryString({
        page,
        page_size: 100,
        sort_by: 'name',
        sort_order: 'asc',
        include_deleted: includeDeleted
      })}`
    )
    items.push(...result.items)
    pages = result.pages
    page += 1
  } while (page <= pages)
  return items
}

const referenceQuery = '?page_size=100&sort_by=name&sort_order=asc'

export const assetApi = {
  list: (query: AssetListQuery = {}) => request<Page<Asset>>(
    `/assets${queryString(query as Record<string, string | number | boolean | undefined>)}`
  ),
  allAssets: (includeDeleted = false) => requestAll<Asset>('/assets', includeDeleted),
  get: (id: string) => request<Asset>(`/assets/${id}`),
  getArchived: (id: string) => request<Asset>(`/archive/assets/${id}`),
  nextInventoryNumber: async () => (
    await request<{ inventory_number: string }>('/assets/next-inventory-number')
  ).inventory_number,
  create: (asset: AssetWrite) => request<Asset>('/assets', {
    method: 'POST', body: JSON.stringify(asset)
  }),
  update: (id: string, asset: AssetWrite) => request<Asset>(`/assets/${id}`, {
    method: 'PUT', body: JSON.stringify(asset)
  }),
  replace: (id: string, replacement: AssetWrite, reason: string | null) => (
    request<AssetReplacement>(`/assets/${id}/replacement`, {
      method: 'POST', body: JSON.stringify({ replacement, reason: reason?.trim() || null })
    })
  ),
  duplicate: (id: string, payload: AssetDuplicateWrite) => request<Asset>(
    `/assets/${id}/duplicate`, { method: 'POST', body: JSON.stringify(payload) }
  ),
  createSeries: (id: string, payload: AssetSeriesWrite) => request<AssetSeriesRead>(
    `/assets/${id}/series`, { method: 'POST', body: JSON.stringify(payload) }
  ),
  remove: (id: string) => request<void>(`/assets/${id}`, { method: 'DELETE' }),
  assetTypes: (includeDeleted = false) => request<Page<AssetType>>(
    `/asset-types${referenceQuery}&include_deleted=${includeDeleted}`
  ),
  allAssetTypes: (includeDeleted = false) => requestAll<AssetType>(
    '/asset-types', includeDeleted
  ),
  createAssetType: (payload: AssetTypeWrite) => request<AssetType>('/asset-types', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateAssetType: (id: string, payload: AssetTypeWrite) => request<AssetType>(
    `/asset-types/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeAssetType: (id: string) => request<void>(
    `/asset-types/${id}`, { method: 'DELETE' }
  ),
  products: (includeDeleted = false) => request<Page<Product>>(
    `/products${referenceQuery}&include_deleted=${includeDeleted}`
  ),
  allProducts: (includeDeleted = false) => requestAll<Product>('/products', includeDeleted),
  getProduct: (id: string) => request<Product>(`/products/${id}`),
  createProduct: (payload: ProductWrite) => request<Product>('/products', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateProduct: (id: string, payload: ProductWrite) => request<Product>(
    `/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  uploadProductImage: (file: File, signal?: AbortSignal) => {
    const data = new FormData()
    data.append('image', file)
    return uploadRequest<ProductImageUpload>('/products/images/upload', data, signal)
  },
  searchProductImages: (query: string, signal?: AbortSignal) => request<ProductImageSearch>(
    `/products/images/search${queryString({ query })}`, { signal }
  ),
  importProductImage: (imageUrl: string, sourceUrl?: string | null, signal?: AbortSignal) => (
    request<ProductImageUpload>('/products/images/import', {
      method: 'POST',
      body: JSON.stringify({ image_url: imageUrl, source_url: sourceUrl || null }),
      signal
    })
  ),
  removeProduct: (id: string) => request<void>(`/products/${id}`, { method: 'DELETE' }),
  locations: () => request<Page<Location>>(`/locations${referenceQuery}`),
  labels: (includeDeleted = false) => request<Page<Label>>(
    `/labels${referenceQuery}&include_deleted=${includeDeleted}`
  ),
  allLabels: (includeDeleted = false) => requestAll<Label>('/labels', includeDeleted),
  createLabel: (payload: LabelWrite) => request<Label>('/labels', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateLabel: (id: string, payload: LabelWrite) => request<Label>(
    `/labels/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeLabel: (id: string) => request<void>(`/labels/${id}`, { method: 'DELETE' }),
  relationships: async (assetId: string) => {
    const [outgoing, incoming] = await Promise.all([
      request<Page<Relationship>>(`/relationships?source_asset_id=${assetId}&page_size=100`),
      request<Page<Relationship>>(`/relationships?target_asset_id=${assetId}&page_size=100`)
    ])
    return [...outgoing.items, ...incoming.items.filter(
      (relationship) => !outgoing.items.some((entry) => entry.id === relationship.id)
    )]
  }
}
