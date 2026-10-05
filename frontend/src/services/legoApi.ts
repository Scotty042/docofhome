import type { LegoDashboard, LegoSet, LegoSetWrite } from '../types/lego'

export interface LegoPage { items: LegoSet[], total: number, count: number, has_more: boolean, next_offset: number | null }
async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/lego${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!response.ok) {
    const body = await response.json().catch(() => ({}))
    const detail = typeof body.detail === 'string' ? body.detail : Array.isArray(body.detail) ? body.detail.map((d: { msg: string }) => d.msg).join(', ') : `Anfrage fehlgeschlagen (${response.status})`
    throw new Error(detail)
  }
  return response.status === 204 ? undefined as T : response.json()
}
export const legoApi = {
  dashboard: () => request<LegoDashboard>('/dashboard'),
  page: (offset = 0) => request<LegoPage>(`/sets?offset=${offset}&limit=100`),
  async list(): Promise<LegoSet[]> {
    const items: LegoSet[] = []
    let offset = 0
    for (;;) {
      const page = await this.page(offset)
      items.push(...page.items)
      if (!page.has_more || page.next_offset === null) return items
      if (page.next_offset <= offset) throw new Error('Ungültige Seitennavigation')
      offset = page.next_offset
    }
  },
  create: (data: LegoSetWrite) => request<LegoSet>('/sets', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: LegoSetWrite) => request<LegoSet>(`/sets/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  remove: (id: string) => request<void>(`/sets/${id}`, { method: 'DELETE' })
}
