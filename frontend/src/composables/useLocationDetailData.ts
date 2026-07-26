import { ref } from 'vue'

import { LocationApiError, locationApi } from '../services/locationApi'
import { loadDirectAssetPage } from '../services/locationAssets'
import type { Asset, Page } from '../types/assets'
import type { Location } from '../types/locations'

interface LocationDetailDependencies {
  getLocation: (id: string) => Promise<Location>
  getAssets: (locationId: string, page: number, pageSize: number) => Promise<Page<Asset>>
}

const defaultDependencies: LocationDetailDependencies = {
  getLocation: (id) => locationApi.get(id, true),
  getAssets: loadDirectAssetPage
}

export function useLocationDetailData(
  dependencies: LocationDetailDependencies = defaultDependencies
) {
  const location = ref<Location | null>(null)
  const assets = ref<Asset[]>([])
  const loading = ref(true)
  const assetsLoading = ref(false)
  const confirmArchive = ref(false)
  const error = ref<string | null>(null)
  const errorStatus = ref<number | null>(null)
  const assetError = ref<string | null>(null)
  const assetTotal = ref(0)
  const assetPages = ref(0)
  const assetPage = ref(1)
  const assetPageSize = ref(25)
  let locationRequestId = 0
  let assetRequestId = 0

  async function loadAssets(requestedLocationId = location.value?.id) {
    if (!requestedLocationId) return
    const requestId = ++assetRequestId
    assetsLoading.value = true
    assetError.value = null
    try {
      const result = await dependencies.getAssets(
        requestedLocationId,
        assetPage.value,
        assetPageSize.value
      )
      if (requestId !== assetRequestId || location.value?.id !== requestedLocationId) return
      assets.value = result.items
      assetTotal.value = result.total
      assetPages.value = result.pages
    } catch (reason) {
      if (requestId !== assetRequestId || location.value?.id !== requestedLocationId) return
      assetError.value = reason instanceof Error
        ? reason.message
        : 'Direkt zugeordnete Assets konnten nicht geladen werden.'
    } finally {
      if (requestId === assetRequestId) assetsLoading.value = false
    }
  }

  function reloadAssetsFromFirstPage() {
    assetPage.value = 1
    void loadAssets()
  }

  function resetLocationState() {
    assetRequestId += 1
    location.value = null
    assets.value = []
    assetPage.value = 1
    assetTotal.value = 0
    assetPages.value = 0
    error.value = null
    errorStatus.value = null
    assetError.value = null
    confirmArchive.value = false
    loading.value = true
    assetsLoading.value = false
  }

  async function loadLocation(id: string) {
    const requestId = ++locationRequestId
    resetLocationState()
    try {
      const record = await dependencies.getLocation(id)
      if (requestId !== locationRequestId) return
      location.value = record
      await loadAssets(id)
    } catch (reason) {
      if (requestId !== locationRequestId) return
      error.value = reason instanceof Error ? reason.message : 'Bereich konnte nicht geladen werden.'
      errorStatus.value = reason instanceof LocationApiError ? reason.status : 0
    } finally {
      if (requestId === locationRequestId) loading.value = false
    }
  }

  return {
    location,
    assets,
    loading,
    assetsLoading,
    confirmArchive,
    error,
    errorStatus,
    assetError,
    assetTotal,
    assetPages,
    assetPage,
    assetPageSize,
    loadAssets,
    reloadAssetsFromFirstPage,
    loadLocation
  }
}
