import { assetApi } from './assetApi'
import type { Asset, Page } from '../types/assets'

export const LOCATION_ASSET_PAGE_SIZES = [10, 25, 50]

export function loadDirectAssetPage(
  locationId: string,
  page: number,
  pageSize: number
): Promise<Page<Asset>> {
  return assetApi.list({
    location_id: locationId,
    page,
    page_size: pageSize,
    sort_by: 'name',
    sort_order: 'asc'
  })
}
