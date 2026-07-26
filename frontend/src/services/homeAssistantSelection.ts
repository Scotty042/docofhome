import type { HomeAssistantEntity } from '../types/homeAssistant'

export type HomeAssistantSelectionFilter = {
  search?: string
  domain?: string | null
  selectedOnly?: boolean
  selectedIds: ReadonlySet<string>
}

export function normalizeSelectedEntityIds(entityIds: Iterable<string>): string[] {
  return [...new Set([...entityIds].map((item) => item.trim()).filter(Boolean))].sort()
}

export function selectionDomains(entities: HomeAssistantEntity[]): string[] {
  return [...new Set(entities.map((entity) => entity.domain))].sort()
}

export function filterSelectionCandidates(
  entities: HomeAssistantEntity[],
  filter: HomeAssistantSelectionFilter
): HomeAssistantEntity[] {
  const search = filter.search?.trim().toLocaleLowerCase() ?? ''
  return entities.filter((entity) => {
    if (filter.domain && entity.domain !== filter.domain) return false
    if (filter.selectedOnly && !filter.selectedIds.has(entity.entity_id)) return false
    if (!search) return true
    return [
      entity.name,
      entity.entity_id,
      entity.device_name,
      entity.area_name,
      entity.platform
    ].some((value) => value?.toLocaleLowerCase().includes(search))
  })
}

export function toggleSelectedEntity(
  selectedIds: ReadonlySet<string>,
  entityId: string
): Set<string> {
  const next = new Set(selectedIds)
  if (next.has(entityId)) next.delete(entityId)
  else next.add(entityId)
  return next
}
