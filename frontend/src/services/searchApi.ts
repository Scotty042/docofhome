import type {
  SearchGroup,
  SearchRequestOptions,
  SearchResponse,
  SearchResult
} from '../types/search'

export class SearchApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message)
  }
}

export function isSafeLocalRoute(route: string): boolean {
  return route.startsWith('/')
    && !route.startsWith('//')
    && !route.includes('\\')
    && !/[\u0000-\u001f\u007f]/u.test(route)
    && !/^\/[a-z][a-z\d+.-]*:/iu.test(route)
}

function sanitizeResult(result: SearchResult): SearchResult | null {
  if (!isSafeLocalRoute(result.route)) return null
  return {
    ...result,
    matched_fields: Array.isArray(result.matched_fields) ? result.matched_fields : []
  }
}

export function sanitizeSearchResponse(response: SearchResponse): SearchResponse {
  const groups: SearchGroup[] = response.groups.map((group) => {
    const results = group.results
      .map(sanitizeResult)
      .filter((result): result is SearchResult => result !== null)
    return { ...group, total: results.length, results }
  })
  return {
    ...response,
    total: groups.reduce((sum, group) => sum + group.results.length, 0),
    groups
  }
}

async function readError(response: Response): Promise<string> {
  let message = `Suche fehlgeschlagen (HTTP ${response.status})`
  try {
    const body = await response.json() as { detail?: string | Array<{ msg?: string }> }
    if (typeof body.detail === 'string') message = body.detail
    if (Array.isArray(body.detail)) {
      message = body.detail.map((entry) => entry.msg).filter(Boolean).join(', ') || message
    }
  } catch {
    // Keep the HTTP fallback for non-JSON responses.
  }
  return message
}

export const searchApi = {
  async search(query: string, options: SearchRequestOptions = {}): Promise<SearchResponse> {
    const params = new URLSearchParams({
      q: query,
      limit_per_type: String(options.limitPerType ?? 5)
    })
    if (options.includeArchived) params.set('include_archived', 'true')
    const response = await fetch(`/api/v1/search?${params.toString()}`, {
      signal: options.signal,
      headers: { Accept: 'application/json' }
    })
    if (!response.ok) throw new SearchApiError(await readError(response), response.status)
    return sanitizeSearchResponse(await response.json() as SearchResponse)
  }
}
