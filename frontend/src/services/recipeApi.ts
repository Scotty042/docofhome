import type { Recipe, RecipeWrite } from '../types/recipe'
async function request<T>(path = '', init?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1/recipes${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...init?.headers } })
  if (!response.ok) throw new Error((await response.json().catch(() => ({}))).detail || `Rezeptanfrage fehlgeschlagen (${response.status})`)
  return response.status === 204 ? undefined as T : response.json()
}
export const recipeApi = {
  list: (q = '') => request<Recipe[]>(q ? `?q=${encodeURIComponent(q)}` : ''),
  create: (data: RecipeWrite) => request<Recipe>('', { method: 'POST', body: JSON.stringify(data) }),
  update: (id: string, data: RecipeWrite) => request<Recipe>(`/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  duplicate: (id: string) => request<Recipe>(`/${id}/duplicate`, { method: 'POST' }),
  remove: (id: string) => request<void>(`/${id}`, { method: 'DELETE' })
}
