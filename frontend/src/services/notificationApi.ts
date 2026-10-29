import type { PushDelivery, PushProvider, PushRead, PushWrite } from '../types/notifications'

async function request<T>(path = '', init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/settings/notifications${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((v: { msg: string }) => v.msg).join(', ') : `Anfrage fehlgeschlagen (${response.status})`
    throw new Error(detail)
  }
  return data
}
export const notificationApi = {
  read: () => request<PushRead>(),
  save: (data: PushWrite) => request<PushRead>('', { method: 'PUT', body: JSON.stringify(data) }),
  history: () => request<PushDelivery[]>('/history'),
  test: (provider: PushProvider, data: PushWrite) => request<{ success: boolean, message: string }>(`/test/${provider}`, { method: 'POST', body: JSON.stringify(data) })
}
