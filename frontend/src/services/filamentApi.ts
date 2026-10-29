import type { FilamentConfig, FilamentSettings, FilamentSlot, FilamentSpool, SpoolWrite } from '../types/filament'
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`/api/v1/filament${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!r.ok) { const body = await r.json().catch(() => ({})); throw new Error(typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail) ? body.detail.map((v: { msg: string }) => v.msg).join(', ') : `Filament-Anfrage fehlgeschlagen (${r.status})`) }
  return r.status === 204 ? undefined as T : r.json()
}
export const filamentApi = {
  async list(): Promise<FilamentSpool[]> { const items: FilamentSpool[] = []; let offset = 0; for (;;) { const page = await request<{ items: FilamentSpool[], has_more: boolean, next_offset: number | null }>(`/spools?archive=all&offset=${offset}&limit=100`); items.push(...page.items); if (!page.has_more || page.next_offset === null) return items; if (page.next_offset <= offset) throw new Error('Ungültige Seitennavigation'); offset = page.next_offset } },
  get: (id: string) => request<FilamentSpool>(`/spools/${id}`),
  create: (data: SpoolWrite) => request<FilamentSpool>('/spools', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: SpoolWrite) => request<FilamentSpool>(`/spools/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  archive: (id: string, cloud = false) => request<{ warning: string | null }>(`/spools/${id}/archive?delete_cloud=${cloud}`, { method: 'POST' }),
  restore: (id: string) => request(`/spools/${id}/restore`, { method: 'POST' }),
  settings: () => request<FilamentSettings>('/settings'),
  saveSettings: (data: FilamentConfig) => request<FilamentSettings>('/settings', { method: 'PUT', body: JSON.stringify(data) }),
  login: (data: object) => request<{ connected: boolean, verification_required: boolean }>('/login', { method: 'POST', body: JSON.stringify(data) }),
  disconnect: () => request<void>('/login', { method: 'DELETE' }),
  sync: () => request<{ count: number, complete: boolean, warning: string | null }>('/sync', { method: 'POST' }),
  slots: () => request<FilamentSlot[]>('/slots'),
  refreshSlots: () => request<{ slots: number, printers_missing: string[] }>('/slots/refresh', { method: 'POST' }),
  bind: (id: string, spool: string | null) => request<void>(`/slots/${id}`, { method: 'PUT', body: JSON.stringify({ spool_id: spool }) }),
  storeImage: (id: string) => request<FilamentSpool>(`/spools/${id}/store-image`, { method: 'POST' }),
  importSnapshot: (data: object) => request('/import', { method: 'POST', body: JSON.stringify(data) }),
  async labels(ids: string[], format: 'pdf' | 'jpg') { const response = await fetch('/api/v1/filament/labels', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ids, format }) }); if (!response.ok) throw new Error((await response.json()).detail || 'Etiketten konnten nicht erstellt werden'); return { blob: await response.blob(), filename: response.headers.get('Content-Disposition')?.match(/filename="([^"]+)"/)?.[1] || `Etiketten.${format}` } }
}
