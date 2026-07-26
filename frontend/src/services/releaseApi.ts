import type {
  AuditEvent,
  DashboardSetting,
  FritzBoxDevice,
  GuidedSetupApply,
  GuidedSetupDraft,
  GuidedSetupDraftWrite,
  GuidedSetupPreview,
  ImportPreview,
  ImportResult,
  NetworkPath,
  PortGenerationPreview,
  PortGroupWrite,
  ServiceWorkload,
  ServiceWorkloadWrite
} from '../types/release'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg).filter(Boolean).join(', ')
    }
  } catch {
    // Keep HTTP fallback.
  }
  return `Anfrage fehlgeschlagen (HTTP ${response.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (!(init?.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(`/api/v1${path}`, { ...init, headers })
  if (!response.ok) throw new Error(await errorMessage(response))
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function upload(file: File): FormData {
  const body = new FormData()
  body.append('file', file)
  return body
}

export const releaseApi = {
  dashboard: () => request<DashboardSetting>('/dashboard/config'),
  saveDashboard: (payload: Pick<DashboardSetting, 'cards'>) => request<DashboardSetting>(
    '/dashboard/config', { method: 'PUT', body: JSON.stringify(payload) }
  ),
  resetDashboard: () => request<DashboardSetting>('/dashboard/config/reset', { method: 'POST' }),
  previewPorts: (deviceId: string, groups: PortGroupWrite[]) => request<PortGenerationPreview>(
    `/network/devices/${deviceId}/ports/preview`,
    { method: 'POST', body: JSON.stringify({ groups }) }
  ),
  generatePorts: (deviceId: string, groups: PortGroupWrite[]) => request<PortGenerationPreview>(
    `/network/devices/${deviceId}/ports/generate`,
    { method: 'POST', body: JSON.stringify({ groups }) }
  ),
  networkPath: (deviceId: string) => request<NetworkPath>(`/network/devices/${deviceId}/path`),
  workloads: () => request<ServiceWorkload[]>('/workloads'),
  createWorkload: (payload: ServiceWorkloadWrite) => request<ServiceWorkload>(
    '/workloads', { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateWorkload: (id: string, payload: ServiceWorkloadWrite) => request<ServiceWorkload>(
    `/workloads/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  archiveWorkload: (id: string) => request<void>(`/workloads/${id}`, { method: 'DELETE' }),
  exportUrl: '/api/v1/portability/export',
  csvExportUrl: (module: string) => `/api/v1/portability/export/${encodeURIComponent(module)}.csv`,
  previewImport: (file: File) => request<ImportPreview>(
    '/portability/import/preview', { method: 'POST', body: upload(file) }
  ),
  applyImport: (file: File, strategy: 'fail' | 'skip') => request<ImportResult>(
    `/portability/import?strategy=${strategy}`, { method: 'POST', body: upload(file) }
  ),
  audit: (query = '') => request<AuditEvent[]>(`/audit-events${query}`),
  fritzBoxDevices: () => request<FritzBoxDevice[]>('/fritzbox/devices'),
  drafts: () => request<GuidedSetupDraft[]>('/guided-setup/drafts'),
  createDraft: (payload: GuidedSetupDraftWrite) => request<GuidedSetupDraft>(
    '/guided-setup/drafts', { method: 'POST', body: JSON.stringify(payload) }
  ),
  updateDraft: (id: string, payload: GuidedSetupDraftWrite) => request<GuidedSetupDraft>(
    `/guided-setup/drafts/${id}`, { method: 'PUT', body: JSON.stringify(payload) }
  ),
  previewDraft: (id: string) => request<GuidedSetupPreview>(
    `/guided-setup/drafts/${id}/preview`
  ),
  applyDraft: (id: string) => request<GuidedSetupApply>(
    `/guided-setup/drafts/${id}/apply`, { method: 'POST' }
  )
}
