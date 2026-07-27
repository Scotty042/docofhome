import type {
  SmartMeterMeasurementPoint,
  SmartMeterMeasurementPointWrite
} from '../types/electrical'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/electrical/smart-meters${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) {
    let message = `Anfrage fehlgeschlagen (HTTP ${response.status})`
    try {
      const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
      if (typeof body.detail === 'string') message = body.detail
      if (Array.isArray(body.detail)) {
        message = body.detail.map((item) => item.msg).filter(Boolean).join(', ') || message
      }
    } catch {
      // Keep HTTP fallback.
    }
    throw new Error(message)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export const smartMeterApi = {
  measurementPoints: (assetId: string) => request<SmartMeterMeasurementPoint[]>(
    `/${encodeURIComponent(assetId)}/measurement-points`
  ),
  createMeasurementPoint: (assetId: string, payload: SmartMeterMeasurementPointWrite) => (
    request<SmartMeterMeasurementPoint>(`/${encodeURIComponent(assetId)}/measurement-points`, {
      method: 'POST', body: JSON.stringify(payload)
    })
  ),
  updateMeasurementPoint: (
    assetId: string,
    pointId: string,
    payload: SmartMeterMeasurementPointWrite
  ) => request<SmartMeterMeasurementPoint>(
    `/${encodeURIComponent(assetId)}/measurement-points/${encodeURIComponent(pointId)}`,
    { method: 'PUT', body: JSON.stringify(payload) }
  ),
  removeMeasurementPoint: (assetId: string, pointId: string) => request<void>(
    `/${encodeURIComponent(assetId)}/measurement-points/${encodeURIComponent(pointId)}`,
    { method: 'DELETE' }
  )
}
