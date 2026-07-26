import type { ProductImageSearchItem } from '../types/assets'

const WIKIMEDIA_API = 'https://commons.wikimedia.org/w/api.php'
const MAX_IMAGE_BYTES = 10 * 1024 * 1024
const ALLOWED_IMAGE_TYPES: Record<string, string> = {
  'image/jpeg': 'jpg',
  'image/png': 'png',
  'image/webp': 'webp',
  'image/gif': 'gif'
}

function allowedUrl(value: string, hosts: ReadonlySet<string>): boolean {
  try {
    const parsed = new URL(value)
    return parsed.protocol === 'https:'
      && !parsed.username
      && !parsed.password
      && (parsed.port === '' || parsed.port === '443')
      && hosts.has(parsed.hostname.toLocaleLowerCase())
  } catch {
    return false
  }
}

const imageHosts = new Set(['upload.wikimedia.org'])
const sourceHosts = new Set(['commons.wikimedia.org'])

function metadataValue(metadata: unknown, key: string): string | null {
  if (!metadata || typeof metadata !== 'object') return null
  const entry = (metadata as Record<string, unknown>)[key]
  if (!entry || typeof entry !== 'object') return null
  const value = (entry as Record<string, unknown>).value
  if (typeof value !== 'string') return null
  const text = value.replace(/<[^>]+>/g, ' ').replace(/&nbsp;/gi, ' ').replace(/&amp;/gi, '&')
  return text.replace(/\s+/g, ' ').trim().slice(0, 300) || null
}

function cleanTitle(value: unknown): string {
  const title = typeof value === 'string' ? value.replace(/^File:/, '') : 'Produktbild'
  return title.replace(/\.[^.]+$/, '').replace(/_/g, ' ').slice(0, 200)
}

export async function searchWikimediaInBrowser(
  query: string,
  options: { signal?: AbortSignal; limit?: number } = {}
): Promise<ProductImageSearchItem[]> {
  const normalized = query.trim()
  if (normalized.length < 2) throw new Error('Bitte mindestens zwei Suchzeichen eingeben.')
  const params = new URLSearchParams({
    action: 'query',
    generator: 'search',
    gsrsearch: normalized,
    gsrnamespace: '6',
    gsrlimit: String(Math.min(Math.max(options.limit ?? 12, 1), 24)),
    prop: 'imageinfo',
    iiprop: 'url|extmetadata',
    iiurlwidth: '360',
    format: 'json',
    formatversion: '2',
    origin: '*'
  })
  const response = await fetch(`${WIKIMEDIA_API}?${params.toString()}`, {
    signal: options.signal,
    headers: { Accept: 'application/json' }
  })
  if (!response.ok) {
    throw new Error(`Die externe Wikimedia-Suche antwortet mit HTTP ${response.status}.`)
  }
  const payload = await response.json() as {
    query?: { pages?: Array<Record<string, unknown>> }
  }
  const pages = Array.isArray(payload.query?.pages) ? payload.query.pages : []
  const items: ProductImageSearchItem[] = []
  for (const page of pages) {
    const rows = page.imageinfo
    if (!Array.isArray(rows) || !rows.length || !rows[0] || typeof rows[0] !== 'object') continue
    const info = rows[0] as Record<string, unknown>
    const imageUrl = typeof info.url === 'string' ? info.url : ''
    const thumbnailUrl = typeof info.thumburl === 'string' ? info.thumburl : imageUrl
    const sourceUrl = typeof info.descriptionurl === 'string' ? info.descriptionurl : ''
    if (!allowedUrl(imageUrl, imageHosts)
      || !allowedUrl(thumbnailUrl, imageHosts)
      || !allowedUrl(sourceUrl, sourceHosts)) continue
    items.push({
      title: cleanTitle(page.title),
      thumbnail_url: thumbnailUrl,
      source_url: sourceUrl,
      image_url: imageUrl,
      license_name: metadataValue(info.extmetadata, 'LicenseShortName'),
      author: metadataValue(info.extmetadata, 'Artist')
    })
  }
  return items
}

export async function downloadWikimediaImageInBrowser(
  item: ProductImageSearchItem,
  options: { signal?: AbortSignal } = {}
): Promise<File> {
  if (!allowedUrl(item.image_url, imageHosts) || !allowedUrl(item.source_url, sourceHosts)) {
    throw new Error('Das Online-Bild stammt nicht von einem freigegebenen Wikimedia-Host.')
  }
  const response = await fetch(item.image_url, { signal: options.signal })
  if (!response.ok) {
    throw new Error(`Der Bilddownload antwortet mit HTTP ${response.status}.`)
  }
  const contentType = (response.headers.get('content-type') ?? '').split(';', 1)[0].toLocaleLowerCase()
  const extension = ALLOWED_IMAGE_TYPES[contentType]
  if (!extension) throw new Error('Der gewählte Treffer ist kein unterstütztes Bildformat.')
  const declaredSize = Number(response.headers.get('content-length') ?? 0)
  if (declaredSize > MAX_IMAGE_BYTES) throw new Error('Das Online-Produktbild ist größer als 10 MB.')
  const blob = await response.blob()
  if (!blob.size) throw new Error('Das Online-Produktbild ist leer.')
  if (blob.size > MAX_IMAGE_BYTES) throw new Error('Das Online-Produktbild ist größer als 10 MB.')
  return new File([blob], `wikimedia-product-image.${extension}`, { type: contentType })
}
