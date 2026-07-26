import type {
  NetworkAddress,
  NetworkAddressWrite,
  NetworkConnection,
  NetworkConnectionWrite,
  NetworkDevice,
  NetworkDeviceCandidate,
  NetworkDeviceWrite,
  NetworkInterface,
  NetworkInterfaceWrite,
  NetworkRole,
  NetworkSegment,
  NetworkSegmentWrite,
  NetworkSummary,
  NetworkTopology
} from '../types/network'

export class NetworkApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

function queryString(values: Record<string, string | boolean | undefined>): string {
  const query = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== '') query.set(key, String(value))
  })
  return query.size ? `?${query.toString()}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/network${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    let message = `Netzwerkanfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg).filter(Boolean).join(', ') || message
      }
    } catch {
      // Keep the safe HTTP fallback for non-JSON responses.
    }
    throw new NetworkApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const networkApi = {
  summary: () => request<NetworkSummary>('/summary'),
  topology: () => request<NetworkTopology>('/topology'),
  candidates: () => request<NetworkDeviceCandidate[]>('/device-candidates'),
  devices: (values: { search?: string; role?: NetworkRole | ''; includeArchived?: boolean } = {}) => (
    request<NetworkDevice[]>(`/devices${queryString({
      search: values.search,
      role: values.role || undefined,
      include_archived: values.includeArchived
    })}`)
  ),
  device: (id: string, includeArchived = false) => request<NetworkDevice>(
    `/devices/${id}${queryString({ include_archived: includeArchived })}`
  ),
  createDevice: (payload: NetworkDeviceWrite) => request<NetworkDevice>('/devices', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateDevice: (id: string, payload: NetworkDeviceWrite) => request<NetworkDevice>(`/devices/${id}`, {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  deleteDevice: (id: string) => request<void>(`/devices/${id}`, { method: 'DELETE' }),
  segments: () => request<NetworkSegment[]>('/segments'),
  createSegment: (payload: NetworkSegmentWrite) => request<NetworkSegment>('/segments', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateSegment: (id: string, payload: NetworkSegmentWrite) => request<NetworkSegment>(`/segments/${id}`, {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  deleteSegment: (id: string) => request<void>(`/segments/${id}`, { method: 'DELETE' }),
  interfaces: (deviceId?: string) => request<NetworkInterface[]>(
    `/interfaces${queryString({ device_id: deviceId })}`
  ),
  createInterface: (payload: NetworkInterfaceWrite) => request<NetworkInterface>('/interfaces', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateInterface: (id: string, payload: NetworkInterfaceWrite) => request<NetworkInterface>(
    `/interfaces/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  deleteInterface: (id: string) => request<void>(`/interfaces/${id}`, { method: 'DELETE' }),
  addresses: (values: { interfaceId?: string; deviceId?: string; segmentId?: string } = {}) => (
    request<NetworkAddress[]>(`/addresses${queryString({
      interface_id: values.interfaceId,
      device_id: values.deviceId,
      segment_id: values.segmentId
    })}`)
  ),
  createAddress: (payload: NetworkAddressWrite) => request<NetworkAddress>('/addresses', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateAddress: (id: string, payload: NetworkAddressWrite) => request<NetworkAddress>(
    `/addresses/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  deleteAddress: (id: string) => request<void>(`/addresses/${id}`, { method: 'DELETE' }),
  connections: (deviceId?: string) => request<NetworkConnection[]>(
    `/connections${queryString({ device_id: deviceId })}`
  ),
  createConnection: (payload: NetworkConnectionWrite) => request<NetworkConnection>('/connections', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateConnection: (id: string, payload: NetworkConnectionWrite) => request<NetworkConnection>(
    `/connections/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  deleteConnection: (id: string) => request<void>(`/connections/${id}`, { method: 'DELETE' })
}
