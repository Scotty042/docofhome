import type { ImmichAssetLink, ImmichImage, ImmichImageQuery } from '../types/immich'
import type { ConfigurationRead } from '../types/settings'

export function selectedImmichAlbumId(
  configuration: Pick<ConfigurationRead, 'integrations'>
): string | null {
  return configuration.integrations.find(
    (integration) => integration.kind === 'immich'
  )?.selected_album_id ?? null
}

export function albumImageQuery(
  albumId: string,
  page: number,
  search: string
): ImmichImageQuery {
  return {
    page,
    page_size: 48,
    album_id: albumId,
    search: search.trim() || undefined
  }
}

export function linkedImmichAssetIds(links: ImmichAssetLink[]): Set<string> {
  return new Set(links.map((link) => link.immich_asset_id))
}
export function prependImmichLink(
  links: ImmichAssetLink[],
  created: ImmichAssetLink
): ImmichAssetLink[] {
  return [created, ...links.filter((link) => link.id !== created.id)]
}

export function formatImmichTimestamp(value: string | null): string {
  if (!value) return 'Aufnahmedatum unbekannt'
  return new Intl.DateTimeFormat('de-DE', {
    dateStyle: 'medium',
    timeStyle: 'short'
  }).format(new Date(value))
}

export function formatImmichDimensions(image: Pick<ImmichImage, 'width' | 'height'>): string {
  if (!image.width || !image.height) return 'Abmessungen unbekannt'
  return `${image.width} × ${image.height} px`
}

export function adjacentImmichImage(
  images: ImmichImage[],
  currentId: string,
  direction: -1 | 1
): ImmichImage | null {
  const currentIndex = images.findIndex((image) => image.immich_asset_id === currentId)
  if (currentIndex < 0) return null
  const targetIndex = currentIndex + direction
  return targetIndex >= 0 && targetIndex < images.length ? images[targetIndex] : null
}
