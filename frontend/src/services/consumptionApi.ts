import type {
  ConsumptionDefaultSeed,
  ConsumptionComparison,
  ConsumptionImportPreview,
  ConsumptionImportResult,
  ConsumptionMeter,
  ConsumptionMeterLive,
  ConsumptionMeterType,
  ConsumptionMeterWrite,
  ConsumptionNote,
  ConsumptionNoteWrite,
  ConsumptionReading,
  ConsumptionReadingReminder,
  ConsumptionReadingWrite,
  ConsumptionSettings,
  ConsumptionSettingsWrite,
  ConsumptionStatistics,
  ConsumptionSummary
} from '../types/consumption'

export class ConsumptionApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

function queryString(values: Record<string, string | number | boolean | undefined | null>): string {
  const params = new URLSearchParams()
  Object.entries(values).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value))
  })
  const serialized = params.toString()
  return serialized ? `?${serialized}` : ''
}

async function errorMessage(response: Response): Promise<string> {
  let message = `Verbrauchsanfrage fehlgeschlagen (HTTP ${response.status})`
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') message = body.detail
    if (Array.isArray(body.detail)) {
      message = body.detail.map((entry) => entry.msg).filter(Boolean).join(', ') || message
    }
  } catch {
    // Keep HTTP fallback.
  }
  return message
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (!(init?.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`/api/v1/consumption${path}`, { ...init, headers })
  if (!response.ok) throw new ConsumptionApiError(await errorMessage(response), response.status)
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function uploadBody(file: File): FormData {
  const body = new FormData()
  body.append('file', file)
  return body
}

export const consumptionApi = {
  summary: () => request<ConsumptionSummary>('/summary'),
  dashboardComparisons: () => request<ConsumptionComparison[]>('/dashboard-comparisons'),
  readingReminders: (daysAhead = 3) => request<ConsumptionReadingReminder[]>(
    `/reading-reminders${queryString({ days_ahead: daysAhead })}`
  ),
  statistics: (months = 12) => request<ConsumptionStatistics>(`/statistics${queryString({ months })}`),
  settings: () => request<ConsumptionSettings>('/settings'),
  updateSettings: (payload: ConsumptionSettingsWrite) => request<ConsumptionSettings>('/settings', {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  seedDefaults: () => request<ConsumptionDefaultSeed>('/default-meters', { method: 'POST' }),
  meters: (query: {
    search?: string
    meter_type?: ConsumptionMeterType
    asset_id?: string
    location_id?: string
    include_archived?: boolean
  } = {}) => request<ConsumptionMeter[]>(`/meters${queryString(query)}`),
  live: (id: string, refresh = false) => request<ConsumptionMeterLive>(
    `/meters/${id}/live${queryString({ refresh: refresh || undefined })}`
  ),
  meter: (id: string, includeArchived = false) => request<ConsumptionMeter>(
    `/meters/${id}${queryString({ include_archived: includeArchived || undefined })}`
  ),
  createMeter: (payload: ConsumptionMeterWrite) => request<ConsumptionMeter>('/meters', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateMeter: (id: string, payload: ConsumptionMeterWrite) => request<ConsumptionMeter>(`/meters/${id}`, {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  removeMeter: (id: string) => request<void>(`/meters/${id}`, { method: 'DELETE' }),
  captureHomeAssistant: (id: string) => request<ConsumptionReading>(
    `/meters/${id}/capture-home-assistant`, { method: 'POST' }
  ),
  readings: (query: {
    meter_id?: string
    start?: string
    end?: string
    limit?: number
  } = {}) => request<ConsumptionReading[]>(`/readings${queryString(query)}`),
  createReading: (payload: ConsumptionReadingWrite) => request<ConsumptionReading>('/readings', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateReading: (id: string, payload: ConsumptionReadingWrite) => request<ConsumptionReading>(`/readings/${id}`, {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  removeReading: (id: string) => request<void>(`/readings/${id}`, { method: 'DELETE' }),
  notes: () => request<ConsumptionNote[]>('/notes'),
  createNote: (payload: ConsumptionNoteWrite) => request<ConsumptionNote>('/notes', {
    method: 'POST', body: JSON.stringify(payload)
  }),
  updateNote: (id: string, payload: ConsumptionNoteWrite) => request<ConsumptionNote>(`/notes/${id}`, {
    method: 'PUT', body: JSON.stringify(payload)
  }),
  removeNote: (id: string) => request<void>(`/notes/${id}`, { method: 'DELETE' }),
  previewImport: (file: File) => request<ConsumptionImportPreview>('/import/preview', {
    method: 'POST', body: uploadBody(file)
  }),
  importFile: (file: File, createMissingMeters = true, overwrite = false) => request<ConsumptionImportResult>(
    `/import${queryString({ create_missing_meters: createMissingMeters, overwrite })}`,
    { method: 'POST', body: uploadBody(file) }
  )
}
