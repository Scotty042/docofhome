import type { AboutInformation, FeedbackResult, FeedbackWrite } from '../types/about'

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail)) {
      return body.detail.map((item) => item.msg).filter(Boolean).join(', ')
    }
  } catch {
    // Keep the generic HTTP message when the response was not JSON.
  }
  return `Anfrage fehlgeschlagen (HTTP ${response.status})`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers }
  })
  if (!response.ok) throw new Error(await errorMessage(response))
  return response.json() as Promise<T>
}

export const aboutApi = {
  read: () => request<AboutInformation>('/about'),
  sendFeedback: (payload: FeedbackWrite) => request<FeedbackResult>(
    '/about/feedback',
    { method: 'POST', body: JSON.stringify(payload) }
  )
}
