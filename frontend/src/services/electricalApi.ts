import type {
  AvailableAssetQuery,
  AvailableElectricalAsset,
  Distribution,
  DistributionArea,
  DistributionAreaWrite,
  DistributionDetail,
  DistributionListQuery,
  DistributionSection,
  DistributionSectionWrite,
  DistributionTreeNode,
  DistributionWrite,
  ElectricalCircuit,
  ElectricalCircuitAsset,
  ElectricalCircuitListQuery,
  ElectricalProtectiveDeviceOption,
  ElectricalCircuitWrite,
  ElectricalConnection,
  ElectricalConnectionWrite,
  ElectricalCabinetComponent,
  ElectricalCabinetComponentWrite,
  ElectricalEndpoint,
  ElectricalAssetPlacement,
  ElectricalAssetPlacementWrite,
  ElectricalMeterPlacement,
  ElectricalMeterPlacementWrite,
  ElectricalRole,
  ElectricalTopology,
  Page,
  ProtectiveDevice,
  ProtectiveDeviceListQuery,
  ProtectiveDevicePlacementWrite,
  ProtectiveDeviceWrite
} from '../types/electrical'

export class ElectricalApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

type QueryValue = string | number | boolean | undefined

function queryString(values: Record<string, QueryValue>): string {
  const query = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value))
  })
  const serialized = query.toString()
  return serialized ? `?${serialized}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/electrical${path}`, {
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
    throw new ElectricalApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const electricalApi = {
  listDistributions: (query: DistributionListQuery = {}) => request<Page<Distribution>>(
    `/distributions${queryString(query as Record<string, QueryValue>)}`
  ),
  distributionTree: (includeDeleted = false) => request<DistributionTreeNode[]>(
    `/distributions/tree${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  getDistribution: (id: string, includeDeleted = false) => request<DistributionDetail>(
    `/distributions/${id}${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  createDistribution: (payload: DistributionWrite) => request<DistributionDetail>(
    '/distributions',
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateDistribution: (id: string, payload: DistributionWrite) => (
    request<DistributionDetail>(`/distributions/${id}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  ),
  moveDistribution: (id: string, parentDistributionId: string | null) => (
    request<DistributionDetail>(`/distributions/${id}/move`, {
      method: 'POST',
      body: JSON.stringify({ parent_distribution_id: parentDistributionId })
    })
  ),
  removeDistribution: (id: string) => request<void>(
    `/distributions/${id}`,
    { method: 'DELETE' }
  ),
  getLayout: (distributionId: string) => request<DistributionSection[]>(
    `/distributions/${distributionId}/layout`
  ),
  createSection: (distributionId: string, payload: DistributionSectionWrite) => (
    request<DistributionSection>(`/distributions/${distributionId}/sections`, {
      method: 'POST', body: JSON.stringify(payload)
    })
  ),
  updateSection: (
    distributionId: string,
    sectionId: string,
    payload: DistributionSectionWrite
  ) => request<DistributionSection>(
    `/distributions/${distributionId}/sections/${sectionId}`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeSection: (distributionId: string, sectionId: string) => request<void>(
    `/distributions/${distributionId}/sections/${sectionId}`,
    { method: 'DELETE' }
  ),
  createArea: (
    distributionId: string,
    sectionId: string,
    payload: DistributionAreaWrite
  ) => request<DistributionArea>(
    `/distributions/${distributionId}/sections/${sectionId}/areas`,
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateArea: (distributionId: string, areaId: string, payload: DistributionAreaWrite) => (
    request<DistributionArea>(`/distributions/${distributionId}/areas/${areaId}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  ),
  removeArea: (distributionId: string, areaId: string) => request<void>(
    `/distributions/${distributionId}/areas/${areaId}`,
    { method: 'DELETE' }
  ),
  allAssetPlacements: () => request<ElectricalAssetPlacement[]>(
    '/distributions/placements/assets'
  ),
  assetPlacements: (distributionId: string) => request<ElectricalAssetPlacement[]>(
    `/distributions/${distributionId}/asset-placements`
  ),
  placeAsset: (distributionId: string, assetId: string, payload: ElectricalAssetPlacementWrite) => (
    request<ElectricalAssetPlacement>(`/distributions/${distributionId}/assets/${assetId}/placement`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  ),
  unplaceAsset: (distributionId: string, assetId: string) => request<void>(
    `/distributions/${distributionId}/assets/${assetId}/placement`,
    { method: 'DELETE' }
  ),
  cabinetComponents: (distributionId: string) => request<ElectricalCabinetComponent[]>(
    `/distributions/${distributionId}/cabinet-components`
  ),
  createCabinetComponent: (
    distributionId: string,
    payload: ElectricalCabinetComponentWrite
  ) => request<ElectricalCabinetComponent>(
    `/distributions/${distributionId}/cabinet-components`,
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateCabinetComponent: (
    distributionId: string,
    componentId: string,
    payload: ElectricalCabinetComponentWrite
  ) => request<ElectricalCabinetComponent>(
    `/distributions/${distributionId}/cabinet-components/${componentId}`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  synchronizePhaseRailContacts: (
    distributionId: string,
    componentId: string,
    protectiveDeviceIds: string[],
    assetIds: string[]
  ) => request<ElectricalCabinetComponent>(
    `/distributions/${distributionId}/cabinet-components/${componentId}/synchronize`,
    {
      method: 'POST',
      body: JSON.stringify({ protective_device_ids: protectiveDeviceIds, asset_ids: assetIds })
    }
  ),
  removeCabinetComponent: (distributionId: string, componentId: string) => request<void>(
    `/distributions/${distributionId}/cabinet-components/${componentId}`,
    { method: 'DELETE' }
  ),
  allMeterPlacements: () => request<ElectricalMeterPlacement[]>(
    '/distributions/placements/meters'
  ),
  meterPlacements: (distributionId: string) => request<ElectricalMeterPlacement[]>(
    `/distributions/${distributionId}/meter-placements`
  ),
  placeMeter: (distributionId: string, meterId: string, payload: ElectricalMeterPlacementWrite) => (
    request<ElectricalMeterPlacement>(
      `/distributions/${distributionId}/meters/${meterId}/placement`,
      { method: 'PUT', body: JSON.stringify(payload) }
    )
  ),
  unplaceMeter: (distributionId: string, meterId: string) => request<void>(
    `/distributions/${distributionId}/meters/${meterId}/placement`,
    { method: 'DELETE' }
  ),
  placeMeterAsset: (
    distributionId: string,
    assetId: string,
    payload: ElectricalMeterPlacementWrite
  ) => request<ElectricalMeterPlacement>(
    `/distributions/${distributionId}/meter-assets/${assetId}/placement`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  unplaceMeterAsset: (distributionId: string, assetId: string) => request<void>(
    `/distributions/${distributionId}/meter-assets/${assetId}/placement`,
    { method: 'DELETE' }
  ),
  placeDevice: (
    distributionId: string,
    deviceId: string,
    payload: ProtectiveDevicePlacementWrite
  ) => request<void>(
    `/distributions/${distributionId}/protective-devices/${deviceId}/placement`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  updateStructuredProtectiveDevice: (
    distributionId: string,
    deviceId: string,
    payload: ProtectiveDeviceWrite
  ) => request<void>(
    `/distributions/${distributionId}/protective-devices/${deviceId}/technical`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  listProtectiveDevices: (query: ProtectiveDeviceListQuery = {}) => (
    request<Page<ProtectiveDevice>>(
      `/protective-devices${queryString(query as Record<string, QueryValue>)}`
    )
  ),
  getProtectiveDevice: (id: string, includeDeleted = false) => request<ProtectiveDevice>(
    `/protective-devices/${id}${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  createProtectiveDevice: (payload: ProtectiveDeviceWrite) => request<ProtectiveDevice>(
    '/protective-devices',
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateProtectiveDevice: (id: string, payload: ProtectiveDeviceWrite) => (
    request<ProtectiveDevice>(`/protective-devices/${id}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  ),
  removeProtectiveDevice: (id: string) => request<void>(
    `/protective-devices/${id}`,
    { method: 'DELETE' }
  ),
  listCircuits: (query: ElectricalCircuitListQuery = {}) => request<Page<ElectricalCircuit>>(
    `/circuits${queryString(query as Record<string, QueryValue>)}`
  ),
  protectiveDeviceOptions: (distributionId: string, circuitId?: string) => request<ElectricalProtectiveDeviceOption[]>(
    `/circuits/protective-device-options${queryString({ distribution_id: distributionId, circuit_id: circuitId })}`
  ),
  getCircuit: (id: string, includeDeleted = false) => request<ElectricalCircuit>(
    `/circuits/${id}${queryString({ include_deleted: includeDeleted || undefined })}`
  ),
  createCircuit: (payload: ElectricalCircuitWrite) => request<ElectricalCircuit>(
    '/circuits',
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateCircuit: (id: string, payload: ElectricalCircuitWrite) => request<ElectricalCircuit>(
    `/circuits/${id}`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeCircuit: (id: string) => request<void>(
    `/circuits/${id}`,
    { method: 'DELETE' }
  ),
  listCircuitAssets: (id: string, includeDeleted = false) => (
    request<ElectricalCircuitAsset[]>(
      `/circuits/${id}/assets${queryString({
        include_deleted: includeDeleted || undefined
      })}`
    )
  ),
  assignCircuitAsset: (id: string, assetId: string) => request<ElectricalCircuitAsset>(
    `/circuits/${id}/assets`,
    { method: 'POST', body: JSON.stringify({ asset_id: assetId }) }
  ),
  removeCircuitAsset: (id: string, assetId: string) => request<void>(
    `/circuits/${id}/assets/${assetId}`,
    { method: 'DELETE' }
  ),
  connectionEndpoints: (page = 1, pageSize = 100, search = '') => (
    request<Page<ElectricalEndpoint>>(
      `/connection-endpoints${queryString({
        page,
        page_size: pageSize,
        search: search || undefined
      })}`
    )
  ),
  topology: () => request<ElectricalTopology>('/topology'),
  createConnection: (payload: ElectricalConnectionWrite) => request<ElectricalConnection>(
    '/connections',
    { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateConnection: (id: string, payload: ElectricalConnectionWrite) => (
    request<ElectricalConnection>(`/connections/${id}`, {
      method: 'PUT', body: JSON.stringify(payload)
    })
  ),
  removeConnection: (id: string) => request<void>(
    `/connections/${id}`,
    { method: 'DELETE' }
  ),
  availableAssets: (query: AvailableAssetQuery) => request<Page<AvailableElectricalAsset>>(
    `/available-assets${queryString({
      role: query.role,
      page: query.page,
      page_size: query.page_size,
      search: query.search,
      sort_by: query.sort_by,
      sort_order: query.sort_order,
      current_component_id: query.current_component_id
    })}`
  )
}

export async function loadAllConnectionEndpoints(
  loadPage = electricalApi.connectionEndpoints
): Promise<ElectricalEndpoint[]> {
  const first = await loadPage(1, 100, '')
  const items = [...first.items]
  for (let page = 2; page <= first.pages; page += 1) {
    const next = await loadPage(page, 100, '')
    items.push(...next.items)
  }
  if (items.length !== first.total) {
    throw new Error(
      `Elektro-Endpunkte unvollständig: ${items.length} von ${first.total} Einträgen geladen.`
    )
  }
  return items
}

export async function loadAllAvailableAssets(
  role: ElectricalRole,
  currentComponentId?: string,
  search = '',
  loadPage = electricalApi.availableAssets
): Promise<AvailableElectricalAsset[]> {
  const first = await loadPage({
    role,
    page: 1,
    page_size: 100,
    search,
    sort_by: 'name',
    sort_order: 'asc',
    current_component_id: currentComponentId
  })
  const items = [...first.items]
  for (let page = 2; page <= first.pages; page += 1) {
    const next = await loadPage({
      role,
      page,
      page_size: 100,
      search,
      sort_by: 'name',
      sort_order: 'asc',
      current_component_id: currentComponentId
    })
    items.push(...next.items)
  }
  if (items.length !== first.total) {
    throw new Error(
      `Asset-Auswahl unvollständig: ${items.length} von ${first.total} Einträgen geladen.`
    )
  }
  return items
}


export async function loadAllProtectiveDevices(
  loadPage = electricalApi.listProtectiveDevices
): Promise<ProtectiveDevice[]> {
  const first = await loadPage({
    page: 1,
    page_size: 100,
    sort_by: 'asset_name',
    sort_order: 'asc'
  })
  const items = [...first.items]
  for (let page = 2; page <= first.pages; page += 1) {
    const next = await loadPage({
      page,
      page_size: 100,
      sort_by: 'asset_name',
      sort_order: 'asc'
    })
    items.push(...next.items)
  }
  if (items.length !== first.total) {
    throw new Error(
      `Schutzgeräte-Auswahl unvollständig: ${items.length} von ${first.total} Einträgen geladen.`
    )
  }
  return items
}
