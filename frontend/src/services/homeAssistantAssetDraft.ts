import type { AssetType, AssetWrite } from '../types/assets'
import type { Location } from '../types/locations'
import type { HomeAssistantDevice, HomeAssistantEntity, HomeAssistantObjectType } from '../types/homeAssistant'

export type HomeAssistantSource = HomeAssistantDevice | HomeAssistantEntity

export function suggestedLocationId(areaName: string | null, locations: Location[]): string | null {
  if (!areaName) return null
  const normalized = areaName.trim().toLocaleLowerCase('de')
  return locations.find((location) => (
    location.name.trim().toLocaleLowerCase('de') === normalized
    || location.path.trim().toLocaleLowerCase('de').endsWith(` / ${normalized}`)
  ))?.id ?? null
}

export function buildHomeAssistantAssetDraft(
  objectType: HomeAssistantObjectType,
  source: HomeAssistantSource,
  assetTypes: AssetType[],
  locations: Location[]
): AssetWrite {
  const device = objectType === 'device' ? source as HomeAssistantDevice : null
  const entity = objectType === 'entity' ? source as HomeAssistantEntity : null
  const details = [
    'Aus Home Assistant angelegt.',
    device?.manufacturer ? `Hersteller: ${device.manufacturer}` : null,
    device?.model ? `Modell: ${device.model}` : null,
    device?.sw_version ? `Software: ${device.sw_version}` : null,
    entity?.entity_id ? `Entität: ${entity.entity_id}` : null,
    entity?.platform ? `Integration: ${entity.platform}` : null
  ].filter((value): value is string => Boolean(value))
  const preferredType = assetTypes.find((type) => (
    type.name.toLocaleLowerCase('de').includes('smart')
    || type.name.toLocaleLowerCase('de').includes('sensor')
  )) ?? assetTypes[0]
  return {
    name: source.name,
    description: details.join('\n'),
    asset_type_id: preferredType?.id ?? '',
    product_id: null,
    location_id: suggestedLocationId(source.area_name, locations),
    serial_number: device?.serial_number ?? null,
    inventory_number: null,
    module_width: null,
    status: 'active',
    label_ids: []
  }
}
